"""R1-EXAM-FIT estimate, with config-field provenance; measured fit is a separate gate."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

GIB = 2**30


def estimate(config: dict, file_bytes: int, context: int = 32768) -> dict:
    if isinstance(file_bytes, bool) or not isinstance(file_bytes, int) or file_bytes <= 0:
        raise ValueError('positive GGUF file size required')
    if context not in (16384, 32768):
        raise ValueError('exam contexts are 32768 and the 16384 CPU-pool fallback')
    root = 'text_config.' if isinstance(config.get('text_config'), dict) else ''
    c = config['text_config'] if root else config
    provenance = {}

    def field(name, *aliases):
        for key in (name, *aliases):
            if c.get(key) is not None:
                provenance[name] = {'field': root + key, 'value': c[key]}
                return c[key]
        raise ValueError(f'cannot estimate: missing config field {root}{name}')

    layers = int(field('num_hidden_layers', 'n_layer'))
    types = c.get('layer_types')
    if types is None and c.get('layers_block_type') is not None:
        types=field('layers_block_type')
    if types is None and c.get('full_attention_interval') and c.get('linear_num_key_heads'):
        interval = int(field('full_attention_interval'))
        types = ['full_attention' if (i+1) % interval == 0 else 'linear_attention' for i in range(layers)]
        provenance['layer_types'] = {'derived_from': root+'full_attention_interval', 'value': types}
    elif types is None:
        model_type = str(c.get('model_type', config.get('model_type', ''))).lower()
        if any(s in model_type for s in ('mamba', 'jamba', 'nemotron_h')):
            raise ValueError('hybrid state model needs explicit layer_types; do not estimate it as attention')
        types = ['sliding_attention' if c.get('sliding_window') else 'full_attention'] * layers
        provenance['layer_types'] = {'derived_from': root+'sliding_window' if c.get('sliding_window') else 'homogeneous attention', 'value': types}
    else:
        provenance['layer_types'] = {'field': root+'layer_types', 'value': types}
    if len(types) != layers or layers < 1:
        raise ValueError('layer_types must match num_hidden_layers')
    shared=int(field('num_kv_shared_layers')) if c.get('num_kv_shared_layers') is not None else 0
    if not 0<=shared<layers: raise ValueError('invalid shared KV layer count')
    head_dim = None
    kv_heads = None
    total, rows = 0, []
    for i, kind in enumerate(types):
        kind = str(kind).lower()
        if shared and i>=layers-shared:
            rows.append({'layer':i,'kind':'shared_kv','tokens':None,'bytes':0});continue
        if kind in ('moe','mlp'):
            size=0;tokens=None
        elif kind=='conv':
            size=4*int(field('hidden_size'))*(int(field('conv_L_cache'))-1);tokens=None
        elif kind in ('full_attention', 'attention', 'sliding_attention', 'sliding_window'):
            if c.get('kv_lora_rank') is not None:
                # Pinned llama.cpp DeepseekV2/GLM4-Moe-Lite converts to one
                # compressed K stream and no separate V cache (MLA).
                rank=int(field('kv_lora_rank'));rope=int(field('qk_rope_head_dim'))
                size=(rank+rope)*context;tokens=context
                total+=size;rows.append({'layer':i,'kind':'compressed_mla','tokens':tokens,'bytes':size})
                continue
            if head_dim is None:
                if c.get('head_dim'):
                    head_dim = int(field('head_dim'))
                else:
                    hidden, heads = int(field('hidden_size')), int(field('num_attention_heads'))
                    if heads < 1 or hidden % heads:
                        raise ValueError('head dimension cannot be inferred exactly')
                    head_dim = hidden // heads
                    provenance['head_dim'] = {'derived_from': [root+'hidden_size', root+'num_attention_heads'], 'value': head_dim}
                kv_heads = int(field('num_key_value_heads', 'num_attention_heads'))
            tokens = min(context, int(field('sliding_window'))) if kind.startswith('sliding') else context
            layer_dim=int(field('global_head_dim')) if kind=='full_attention' and c.get('global_head_dim') is not None else head_dim
            layer_heads=int(field('num_global_key_value_heads')) if kind=='full_attention' and c.get('num_global_key_value_heads') is not None else kv_heads
            size = 2 * layer_heads * layer_dim * tokens  # declared q8_0 approximation: 1 byte
        elif kind in ('linear_attention', 'deltanet', 'gated_delta_net'):
            if c.get('fixed_state_bytes_per_layer') is not None:
                size = int(field('fixed_state_bytes_per_layer'))
            else:
                kh = int(field('linear_num_key_heads')); kd = int(field('linear_key_head_dim'))
                vh = int(field('linear_num_value_heads')); vd = int(field('linear_value_head_dim'))
                kernel = int(field('linear_conv_kernel_dim'))
                size = 4 * (vh*kd*vd + (kernel-1)*(2*kh*kd + vh*vd))
            tokens = None
        elif kind in ('mamba', 'ssm'):
            if c.get('fixed_state_bytes_per_layer') is not None:
                size = int(field('fixed_state_bytes_per_layer'))
            else:
                if c.get('mamba_num_heads') is not None and c.get('mamba_head_dim') is not None:
                    inner=int(field('mamba_num_heads'))*int(field('mamba_head_dim'))
                    provenance['mamba_inner_size']={'derived_from':[root+'mamba_num_heads',root+'mamba_head_dim'],'value':inner}
                else: inner = int(field('mamba_inner_size', 'intermediate_size'))
                state = int(field('mamba_d_state', 'state_size', 'ssm_state_size'))
                conv = int(field('mamba_d_conv', 'conv_kernel'))
                groups=int(field('n_groups')) if c.get('n_groups') is not None else 0
                size = 4 * (inner*state+(conv-1)*(inner+2*groups*state))
            tokens = None
        else:
            raise ValueError(f'unknown layer type {kind!r}; fixed-state provenance required')
        if size < 0 or (size==0 and kind not in ('moe','mlp')):
            raise ValueError('non-positive KV/state estimate')
        total += size
        rows.append({'layer': i, 'kind': kind, 'tokens': tokens, 'bytes': size})
    buffers = int(1.5 * GIB)
    required = file_bytes + total + buffers
    return {'schema': 'exam_fit/v1', 'context': context, 'gguf_bytes': file_bytes,
            'kv_and_state_bytes': total, 'compute_buffer_bytes': buffers,
            'total_bytes': required, 'limit_bytes': int(23.5*GIB),
            'estimated_admissible': required <= 23.5*GIB, 'measured_fit': False,
            'kv_precision': 'q8_0', 'declared_attention_bytes_per_element': 1,
            'fixed_state_precision': 'float32', 'config_fields': provenance, 'layers': rows}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', required=True);p.add_argument('--file-bytes', type=int, required=True)
    p.add_argument('--context',type=int,default=32768,choices=[32768,16384])
    a=p.parse_args(argv);print(json.dumps(estimate(json.loads(Path(a.config).read_text()),a.file_bytes,a.context),indent=2))

if __name__ == '__main__': main()
