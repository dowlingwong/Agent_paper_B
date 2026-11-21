# AOT ID: ['0_backward']
from ctypes import c_void_p, c_long, c_int
import torch
import math
import random
import os
import tempfile
from math import inf, nan
from torch._inductor.hooks import run_intermediate_hooks
from torch._inductor.utils import maybe_profile
from torch._inductor.codegen.memory_planning import _align as align
from torch import device, empty_strided
from torch._inductor.async_compile import AsyncCompile
from torch._inductor.select_algorithm import extern_kernels
from torch._inductor.codegen.multi_kernel import MultiKernelCall
import triton
import triton.language as tl
from torch._inductor.runtime.triton_heuristics import (
    grid,
    split_scan_grid,
    grid_combo_kernels,
    start_graph,
    end_graph,
    cooperative_reduction_grid,
)
from torch._C import _cuda_getCurrentRawStream as get_raw_stream
from torch._C import _cuda_getCurrentRawStream as get_raw_stream

aten = torch.ops.aten
inductor_ops = torch.ops.inductor
_quantized = torch.ops._quantized
assert_size_stride = torch._C._dynamo.guards.assert_size_stride
empty_strided_cpu = torch._C._dynamo.guards._empty_strided_cpu
empty_strided_cuda = torch._C._dynamo.guards._empty_strided_cuda
empty_strided_xpu = torch._C._dynamo.guards._empty_strided_xpu
reinterpret_tensor = torch._C._dynamo.guards._reinterpret_tensor
alloc_from_pool = torch.ops.inductor._alloc_from_pool
async_compile = AsyncCompile()
empty_strided_p2p = torch._C._distributed_c10d._SymmetricMemory.empty_strided_p2p


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/e3/ce3sbwtpzzhg6xeoxra7mbodmoja6ufqih2aukl55puhh4pm6t3d.py
# Topologically Sorted Source Nodes: [loss, logits_1, truediv, tanh], Original ATen: [aten.nll_loss_backward, aten.nll_loss_forward, aten._to_copy, aten.div, aten.tanh, aten._log_softmax, aten._log_softmax_backward_data, aten.mul, aten.tanh_backward]
# Source node to ATen node mapping:
#   logits_1 => convert_element_type_184
#   loss => full_default, full_default_1, sub, sub_1
#   tanh => tanh
#   truediv => div
# Graph fragment:
#   %div_2 : [num_users=1] = call_function[target=torch.ops.aten.div.Tensor](args = (%tangents_1, %convert_element_type_185), kwargs = {})
#   %ne_3 : [num_users=2] = call_function[target=torch.ops.aten.ne.Scalar](args = (%unsqueeze_16, -1), kwargs = {})
#   %full_default : [num_users=1] = call_function[target=torch.ops.aten.full.default](args = ([], 0), kwargs = {dtype: torch.int64, layout: torch.strided, device: cuda:0, pin_memory: False})
#   %where_2 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%ne_3, %unsqueeze_16, %full_default), kwargs = {})
#   %scatter_upon_const_tensor : [num_users=1] = call_function[target=torch._inductor.fx_passes.post_grad.scatter_upon_const_tensor](args = (), kwargs = {shape: [32768, 8192], background_val: 0, dtype: torch.float32, dim: 1, selector: %where_2, val: -1.0})
#   %full_default_1 : [num_users=5] = call_function[target=torch.ops.aten.full.default](args = ([], 0.0), kwargs = {dtype: torch.float32, layout: torch.strided, device: cuda:0, pin_memory: False})
#   %where_3 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%ne_3, %div_2, %full_default_1), kwargs = {})
#   %mul_93 : [num_users=2] = call_function[target=torch.ops.aten.mul.Tensor](args = (%scatter_upon_const_tensor, %where_3), kwargs = {})
#   %convert_element_type_184 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%view_118, torch.float32), kwargs = {})
#   %div : [num_users=1] = call_function[target=torch.ops.aten.div.Tensor](args = (%convert_element_type_184, 15), kwargs = {})
#   %tanh : [num_users=2] = call_function[target=torch.ops.aten.tanh.default](args = (%div,), kwargs = {})
#   %sub : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (%view_119, %amax), kwargs = {})
#   %sub_1 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (%sub, %log), kwargs = {})
#   %exp_1 : [num_users=1] = call_function[target=torch.ops.aten.exp.default](args = (%sub_1,), kwargs = {})
#   %sum_4 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mul_93, [1], True), kwargs = {})
#   %mul_94 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%exp_1, %sum_4), kwargs = {})
#   %sub_2 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (%mul_93, %mul_94), kwargs = {})
#   %mul_95 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%view_121, 15), kwargs = {})
#   %mul_96 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%tanh, %tanh), kwargs = {})
#   %sub_3 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (1, %mul_96), kwargs = {})
#   %mul_97 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%mul_95, %sub_3), kwargs = {})
#   %div_3 : [num_users=1] = call_function[target=torch.ops.aten.div.Tensor](args = (%mul_97, 15), kwargs = {})
#   %convert_element_type_186 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%div_3, torch.bfloat16), kwargs = {})
triton_red_fused__log_softmax__log_softmax_backward_data__to_copy_div_mul_nll_loss_backward_nll_loss_forward_tanh_tanh_backward_0 = async_compile.triton('triton_red_fused__log_softmax__log_softmax_backward_data__to_copy_div_mul_nll_loss_backward_nll_loss_forward_tanh_tanh_backward_0', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.reduction(
    size_hints={'x': 32768, 'r': 8192},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*i64', 'in_ptr1': '*fp32', 'in_ptr2': '*fp32', 'in_ptr3': '*fp32', 'in_ptr4': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_red_fused__log_softmax__log_softmax_backward_data__to_copy_div_mul_nll_loss_backward_nll_loss_forward_tanh_tanh_backward_0', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 8, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_red_fused__log_softmax__log_softmax_backward_data__to_copy_div_mul_nll_loss_backward_nll_loss_forward_tanh_tanh_backward_0(in_out_ptr0, in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, xnumel, rnumel, XBLOCK : tl.constexpr, RBLOCK : tl.constexpr):
    xnumel = 32768
    rnumel = 8192
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:, None]
    xmask = tl.full([XBLOCK, RBLOCK], True, tl.int1)
    rbase = tl.arange(0, RBLOCK)[None, :]
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (x0), None, eviction_policy='evict_last')
    tmp10 = tl.load(in_ptr1 + (0))
    tmp11 = tl.broadcast_to(tmp10, [XBLOCK, RBLOCK])
    tmp12 = tl.load(in_ptr2 + (0))
    tmp13 = tl.broadcast_to(tmp12, [XBLOCK, RBLOCK])
    _tmp18 = tl.full([XBLOCK, RBLOCK], 0, tl.float32)
    for roffset in range(0, rnumel, RBLOCK):
        rindex = roffset + rbase
        rmask = rindex < rnumel
        r1 = rindex
        tmp1 = tl.full([1, 1], -1, tl.int64)
        tmp2 = tmp0 != tmp1
        tmp3 = tl.full([1, 1], 0, tl.int64)
        tmp4 = tl.where(tmp2, tmp0, tmp3)
        tmp5 = r1
        tmp6 = tmp4 == tmp5
        tmp7 = -1.0
        tmp8 = 0.0
        tmp9 = tl.where(tmp6, tmp7, tmp8)
        tmp14 = tmp11 / tmp13
        tmp15 = tl.where(tmp2, tmp14, tmp8)
        tmp16 = tmp9 * tmp15
        tmp17 = tl.broadcast_to(tmp16, [XBLOCK, RBLOCK])
        tmp19 = _tmp18 + tmp17
        _tmp18 = tl.where(rmask, tmp19, _tmp18)
    tmp18 = tl.sum(_tmp18, 1)[:, None]
    tmp29 = tl.load(in_ptr1 + (0))
    tmp30 = tl.broadcast_to(tmp29, [XBLOCK, RBLOCK])
    tmp31 = tl.load(in_ptr2 + (0))
    tmp32 = tl.broadcast_to(tmp31, [XBLOCK, RBLOCK])
    tmp43 = tl.load(in_ptr3 + (x0), None, eviction_policy='evict_last')
    tmp45 = tl.load(in_ptr4 + (x0), None, eviction_policy='evict_last')
    for roffset in range(0, rnumel, RBLOCK):
        rindex = roffset + rbase
        rmask = rindex < rnumel
        r1 = rindex
        tmp36 = tl.load(in_out_ptr0 + (r1 + 8192*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp20 = tl.full([1, 1], -1, tl.int64)
        tmp21 = tmp0 != tmp20
        tmp22 = tl.full([1, 1], 0, tl.int64)
        tmp23 = tl.where(tmp21, tmp0, tmp22)
        tmp24 = r1
        tmp25 = tmp23 == tmp24
        tmp26 = -1.0
        tmp27 = 0.0
        tmp28 = tl.where(tmp25, tmp26, tmp27)
        tmp33 = tmp30 / tmp32
        tmp34 = tl.where(tmp21, tmp33, tmp27)
        tmp35 = tmp28 * tmp34
        tmp37 = tmp36.to(tl.float32)
        tmp38 = 0.06666666666666667
        tmp39 = tmp37 * tmp38
        tmp40 = libdevice.tanh(tmp39)
        tmp41 = 15.0
        tmp42 = tmp40 * tmp41
        tmp44 = tmp42 - tmp43
        tmp46 = tmp44 - tmp45
        tmp47 = tl_math.exp(tmp46)
        tmp48 = tmp47 * tmp18
        tmp49 = tmp35 - tmp48
        tmp50 = tmp49 * tmp41
        tmp51 = tmp40 * tmp40
        tmp52 = 1.0
        tmp53 = tmp52 - tmp51
        tmp54 = tmp50 * tmp53
        tmp55 = tmp54 * tmp38
        tmp56 = tmp55.to(tl.float32)
        tl.store(in_out_ptr0 + (r1 + 8192*x0), tmp56, rmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/66/c6675i3n7cpfcvlnlx64iqztxy7pqxglp4zlha2etmfrp27of5ov.py
# Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
# Source node to ATen node mapping:
# Graph fragment:
#   %convert_element_type_191 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mm_40, torch.float32), kwargs = {})
triton_poi_fused__to_copy_1 = async_compile.triton('triton_poi_fused__to_copy_1', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.pointwise(
    size_hints={'x': 4194304}, 
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*bf16', 'out_ptr0': '*fp32', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused__to_copy_1', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 1, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused__to_copy_1(in_ptr0, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 3145728
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (x0), None).to(tl.float32)
    tmp1 = tmp0.to(tl.float32)
    tl.store(out_ptr0 + (x0), tmp1, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/ro/crovwskez7pvsyiedprxdfttlvyusayu6d6mjiflwycemiqs3rt4.py
# Topologically Sorted Source Nodes: [x_38], Original ATen: [aten._to_copy, aten.mul, aten.sum, aten.div, aten.pow, aten.add]
# Source node to ATen node mapping:
#   x_38 => convert_element_type_179
# Graph fragment:
#   %convert_element_type_192 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%view_123, torch.float32), kwargs = {})
#   %convert_element_type_179 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_69, torch.float32), kwargs = {})
#   %mul_98 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_192, %convert_element_type_179), kwargs = {})
#   %mul_99 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_192, %rsqrt_25), kwargs = {})
#   %sum_5 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mul_98, [2], True), kwargs = {dtype: torch.float32})
#   %div_4 : [num_users=1] = call_function[target=torch.ops.aten.div.Scalar](args = (%expand_12, 384), kwargs = {})
#   %pow_34 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_179, 1.0), kwargs = {})
#   %mul_102 : [num_users=1] = call_function[target=torch.ops.aten.mul.Scalar](args = (%pow_34, 2.0), kwargs = {})
#   %mul_103 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%div_4, %mul_102), kwargs = {})
#   %add_71 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_99, %mul_103), kwargs = {})
#   %convert_element_type_193 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_71, torch.bfloat16), kwargs = {})
triton_per_fused__to_copy_add_div_mul_pow_sum_2 = async_compile.triton('triton_per_fused__to_copy_add_div_mul_pow_sum_2', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 32768, 'r': 512},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'in_ptr1': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_div_mul_pow_sum_2', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': True, 'num_load': 3, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_div_mul_pow_sum_2(in_out_ptr0, in_ptr0, in_ptr1, xnumel, rnumel):
    xnumel = 32768
    XBLOCK: tl.constexpr = 1
    rnumel = 384
    RBLOCK: tl.constexpr = 512
    xoffset = tl.program_id(0) * XBLOCK
    xindex = tl.full([1], xoffset, tl.int32)
    xmask = tl.full([RBLOCK], True, tl.int1)
    rindex = tl.arange(0, RBLOCK)[:]
    roffset = 0
    rmask = rindex < rnumel
    r1 = rindex
    x0 = xindex
    tmp0 = tl.load(in_out_ptr0 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp2 = tl.load(in_ptr0 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp9 = tl.load(in_ptr1 + (x0), None, eviction_policy='evict_last')
    tmp1 = tmp0.to(tl.float32)
    tmp3 = tmp2.to(tl.float32)
    tmp4 = tmp1 * tmp3
    tmp5 = tl.broadcast_to(tmp4, [RBLOCK])
    tmp7 = tl.where(rmask, tmp5, 0)
    tmp8 = triton_helpers.promote_to_tensor(tl.sum(tmp7, 0))
    tmp10 = tmp1 * tmp9
    tmp11 = -0.5
    tmp12 = tmp8 * tmp11
    tmp13 = tmp9 * tmp9
    tmp14 = tmp13 * tmp9
    tmp15 = tmp12 * tmp14
    tmp16 = 0.0026041666666666665
    tmp17 = tmp15 * tmp16
    tmp18 = 2.0
    tmp19 = tmp3 * tmp18
    tmp20 = tmp17 * tmp19
    tmp21 = tmp10 + tmp20
    tmp22 = tmp21.to(tl.float32)
    tl.store(in_out_ptr0 + (r1 + 384*x0), tmp22, rmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/dy/cdyzvszqdo4xiogplf3n3bxchrb6glow3ncqypgpxyt5jcwu3rfn.py
# Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
# Source node to ATen node mapping:
# Graph fragment:
#   %convert_element_type_199 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mm_42, torch.float32), kwargs = {})
triton_poi_fused__to_copy_3 = async_compile.triton('triton_poi_fused__to_copy_3', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.pointwise(
    size_hints={'x': 1048576}, 
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*bf16', 'out_ptr0': '*fp32', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused__to_copy_3', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 1, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused__to_copy_3(in_ptr0, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 589824
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (x0), None).to(tl.float32)
    tmp1 = tmp0.to(tl.float32)
    tl.store(out_ptr0 + (x0), tmp1, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/on/conabqeqqytrj6rfvyjk27n46ovjii2ady6hszdldzljv76jikva.py
# Topologically Sorted Source Nodes: [relu_5, x_35], Original ATen: [aten._to_copy, aten.relu, aten.pow, aten.mul, aten.threshold_backward]
# Source node to ATen node mapping:
#   relu_5 => relu_5
#   x_35 => convert_element_type_174
# Graph fragment:
#   %convert_element_type_198 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%view_125, torch.float32), kwargs = {})
#   %relu_5 : [num_users=2] = call_function[target=torch.ops.aten.relu.default](args = (%view_114,), kwargs = {})
#   %convert_element_type_174 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%relu_5, torch.float32), kwargs = {})
#   %pow_35 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_174, 1.0), kwargs = {})
#   %mul_104 : [num_users=1] = call_function[target=torch.ops.aten.mul.Scalar](args = (%pow_35, 2.0), kwargs = {})
#   %mul_105 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_198, %mul_104), kwargs = {})
#   %convert_element_type_200 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul_105, torch.bfloat16), kwargs = {})
#   %le : [num_users=1] = call_function[target=torch.ops.aten.le.Scalar](args = (%relu_5, 0), kwargs = {})
#   %full_default_5 : [num_users=6] = call_function[target=torch.ops.aten.full.default](args = ([], 0.0), kwargs = {dtype: torch.bfloat16, layout: torch.strided, device: cuda:0, pin_memory: False})
#   %where_4 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%le, %full_default_5, %convert_element_type_200), kwargs = {})
triton_poi_fused__to_copy_mul_pow_relu_threshold_backward_4 = async_compile.triton('triton_poi_fused__to_copy_mul_pow_relu_threshold_backward_4', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.pointwise(
    size_hints={'x': 67108864}, 
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused__to_copy_mul_pow_relu_threshold_backward_4', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 2, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused__to_copy_mul_pow_relu_threshold_backward_4(in_out_ptr0, in_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 50331648
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = xindex
    tmp0 = tl.load(in_out_ptr0 + (x0), None).to(tl.float32)
    tmp5 = tl.load(in_ptr0 + (x0), None).to(tl.float32)
    tmp1 = tl.full([1], 0, tl.int32)
    tmp2 = triton_helpers.maximum(tmp1, tmp0)
    tmp3 = 0.0
    tmp4 = tmp2 <= tmp3
    tmp6 = tmp5.to(tl.float32)
    tmp7 = tmp2.to(tl.float32)
    tmp8 = 2.0
    tmp9 = tmp7 * tmp8
    tmp10 = tmp6 * tmp9
    tmp11 = tmp10.to(tl.float32)
    tmp12 = tl.where(tmp4, tmp3, tmp11)
    tl.store(in_out_ptr0 + (x0), tmp12, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/sv/csvticfmrhuezxanauuichm7w7snscb5x4pnnr6zhf3kd2lryywx.py
# Topologically Sorted Source Nodes: [rms_norm_24], Original ATen: [aten._to_copy, aten.mul, aten.sum, aten.div, aten.pow, aten.add]
# Source node to ATen node mapping:
#   rms_norm_24 => convert_element_type_169
# Graph fragment:
#   %convert_element_type_206 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%view_127, torch.float32), kwargs = {})
#   %convert_element_type_169 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_67, torch.float32), kwargs = {})
#   %mul_106 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_206, %convert_element_type_169), kwargs = {})
#   %mul_107 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_206, %rsqrt_24), kwargs = {})
#   %sum_6 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mul_106, [2], True), kwargs = {dtype: torch.float32})
#   %div_5 : [num_users=1] = call_function[target=torch.ops.aten.div.Scalar](args = (%expand_13, 384), kwargs = {})
#   %pow_37 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_169, 1.0), kwargs = {})
#   %mul_110 : [num_users=1] = call_function[target=torch.ops.aten.mul.Scalar](args = (%pow_37, 2.0), kwargs = {})
#   %mul_111 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%div_5, %mul_110), kwargs = {})
#   %add_72 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_107, %mul_111), kwargs = {})
#   %convert_element_type_207 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_72, torch.bfloat16), kwargs = {})
#   %add_73 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%convert_element_type_193, %convert_element_type_207), kwargs = {})
triton_per_fused__to_copy_add_div_mul_pow_sum_5 = async_compile.triton('triton_per_fused__to_copy_add_div_mul_pow_sum_5', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 32768, 'r': 512},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_div_mul_pow_sum_5', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': True, 'num_load': 4, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_div_mul_pow_sum_5(in_out_ptr0, in_ptr0, in_ptr1, in_ptr2, xnumel, rnumel):
    xnumel = 32768
    XBLOCK: tl.constexpr = 1
    rnumel = 384
    RBLOCK: tl.constexpr = 512
    xoffset = tl.program_id(0) * XBLOCK
    xindex = tl.full([1], xoffset, tl.int32)
    xmask = tl.full([RBLOCK], True, tl.int1)
    rindex = tl.arange(0, RBLOCK)[:]
    roffset = 0
    rmask = rindex < rnumel
    r1 = rindex
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp2 = tl.load(in_ptr1 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp9 = tl.load(in_out_ptr0 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp10 = tl.load(in_ptr2 + (x0), None, eviction_policy='evict_last')
    tmp1 = tmp0.to(tl.float32)
    tmp3 = tmp2.to(tl.float32)
    tmp4 = tmp1 * tmp3
    tmp5 = tl.broadcast_to(tmp4, [RBLOCK])
    tmp7 = tl.where(rmask, tmp5, 0)
    tmp8 = triton_helpers.promote_to_tensor(tl.sum(tmp7, 0))
    tmp11 = tmp1 * tmp10
    tmp12 = -0.5
    tmp13 = tmp8 * tmp12
    tmp14 = tmp10 * tmp10
    tmp15 = tmp14 * tmp10
    tmp16 = tmp13 * tmp15
    tmp17 = 0.0026041666666666665
    tmp18 = tmp16 * tmp17
    tmp19 = 2.0
    tmp20 = tmp3 * tmp19
    tmp21 = tmp18 * tmp20
    tmp22 = tmp11 + tmp21
    tmp23 = tmp22.to(tl.float32)
    tmp24 = tmp9 + tmp23
    tl.store(in_out_ptr0 + (r1 + 384*x0), tmp24, rmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/h3/ch373snnm7d6ip5lhitndqtzjcqta7d26tujprz2jr74jt4ics3a.py
# Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
# Source node to ATen node mapping:
# Graph fragment:
#   %convert_element_type_212 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mm_46, torch.float32), kwargs = {})
triton_poi_fused__to_copy_6 = async_compile.triton('triton_poi_fused__to_copy_6', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.pointwise(
    size_hints={'x': 262144}, 
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*bf16', 'out_ptr0': '*fp32', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused__to_copy_6', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 1, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused__to_copy_6(in_ptr0, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 147456
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (x0), None).to(tl.float32)
    tmp1 = tmp0.to(tl.float32)
    tl.store(out_ptr0 + (x0), tmp1, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/og/cogxf7b6admsw5iqx4gxjaffo4sfx23i3twy4hap7tlskg56db42.py
# Topologically Sorted Source Nodes: [k_27], Original ATen: [aten._to_copy, aten.mul, aten.sum]
# Source node to ATen node mapping:
#   k_27 => convert_element_type_164
# Graph fragment:
#   %convert_element_type_213 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%squeeze_2, torch.float32), kwargs = {})
#   %convert_element_type_164 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%cat_11, torch.float32), kwargs = {})
#   %mul_112 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_213, %convert_element_type_164), kwargs = {})
#   %sum_7 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mul_112, [3], True), kwargs = {dtype: torch.float32})
triton_per_fused__to_copy_mul_sum_7 = async_compile.triton('triton_per_fused__to_copy_mul_sum_7', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 131072, 'r': 128},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'out_ptr0': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_mul_sum_7', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 2, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_mul_sum_7(in_ptr0, in_ptr1, out_ptr0, xnumel, rnumel, XBLOCK : tl.constexpr):
    xnumel = 98304
    rnumel = 128
    RBLOCK: tl.constexpr = 128
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:, None]
    xmask = tl.full([XBLOCK, RBLOCK], True, tl.int1)
    rindex = tl.arange(0, RBLOCK)[None, :]
    roffset = 0
    rmask = tl.full([XBLOCK, RBLOCK], True, tl.int1)
    r1 = rindex
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (r1 + 128*x0), None).to(tl.float32)
    tmp2 = tl.load(in_ptr1 + (r1 + 128*x0), None).to(tl.float32)
    tmp1 = tmp0.to(tl.float32)
    tmp3 = tmp2.to(tl.float32)
    tmp4 = tmp1 * tmp3
    tmp5 = tl.broadcast_to(tmp4, [XBLOCK, RBLOCK])
    tmp7 = tl.sum(tmp5, 1)[:, None]
    tl.store(out_ptr0 + (x0), tmp7, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/vc/cvcgdfv5humjuybser2cbumabzpebdybyr6b75sn3eqhszg2y3qr.py
# Topologically Sorted Source Nodes: [neg], Original ATen: [aten.mul, aten.neg, aten.add]
# Source node to ATen node mapping:
#   neg => neg
# Graph fragment:
#   %mul_124 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%slice_33, %slice_2), kwargs = {})
#   %neg : [num_users=12] = call_function[target=torch.ops.aten.neg.default](args = (%slice_4,), kwargs = {})
#   %mul_125 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%slice_33, %neg), kwargs = {})
#   %mul_126 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%slice_32, %slice_4), kwargs = {})
#   %add_76 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_124, %mul_126), kwargs = {})
#   %mul_127 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%slice_32, %slice_2), kwargs = {})
#   %add_77 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_125, %mul_127), kwargs = {})
#   %mul_128 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%slice_35, %slice_2), kwargs = {})
#   %mul_129 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%slice_35, %neg), kwargs = {})
#   %mul_130 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%slice_34, %slice_4), kwargs = {})
#   %add_79 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_128, %mul_130), kwargs = {})
#   %mul_131 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%slice_34, %slice_2), kwargs = {})
#   %add_80 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_129, %mul_131), kwargs = {})
triton_poi_fused_add_mul_neg_8 = async_compile.triton('triton_poi_fused_add_mul_neg_8', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.pointwise(
    size_hints={'x': 8388608}, 
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*bf16', 'in_ptr1': '*fp32', 'in_ptr2': '*fp32', 'in_ptr3': '*bf16', 'in_ptr4': '*bf16', 'in_ptr5': '*bf16', 'in_ptr6': '*bf16', 'in_ptr7': '*fp32', 'in_ptr8': '*fp32', 'in_ptr9': '*bf16', 'out_ptr0': '*bf16', 'out_ptr1': '*bf16', 'out_ptr2': '*bf16', 'out_ptr3': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_add_mul_neg_8', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 14, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_add_mul_neg_8(in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, in_ptr5, in_ptr6, in_ptr7, in_ptr8, in_ptr9, out_ptr0, out_ptr1, out_ptr2, out_ptr3, xnumel, XBLOCK : tl.constexpr):
    xnumel = 6291456
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = (xindex % 64)
    x4 = xindex // 64
    x2 = ((xindex // 192) % 2048)
    x5 = xindex
    tmp0 = tl.load(in_ptr0 + (64 + x0 + 128*x4), None).to(tl.float32)
    tmp2 = tl.load(in_ptr1 + (x4), None, eviction_policy='evict_last')
    tmp4 = tl.load(in_ptr2 + (x4), None, eviction_policy='evict_last')
    tmp12 = tl.load(in_ptr3 + (64 + x0 + 128*x4), None).to(tl.float32)
    tmp19 = tl.load(in_ptr4 + (x0 + 64*x2), None, eviction_policy='evict_last').to(tl.float32)
    tmp21 = tl.load(in_ptr0 + (x0 + 128*x4), None).to(tl.float32)
    tmp24 = tl.load(in_ptr3 + (x0 + 128*x4), None).to(tl.float32)
    tmp30 = tl.load(in_ptr5 + (x0 + 64*x2), None, eviction_policy='evict_last').to(tl.float32)
    tmp37 = tl.load(in_ptr6 + (64 + x0 + 128*x4), None).to(tl.float32)
    tmp39 = tl.load(in_ptr7 + (x4), None, eviction_policy='evict_last')
    tmp41 = tl.load(in_ptr8 + (x4), None, eviction_policy='evict_last')
    tmp47 = tl.load(in_ptr9 + (64 + x0 + 128*x4), None).to(tl.float32)
    tmp54 = tl.load(in_ptr6 + (x0 + 128*x4), None).to(tl.float32)
    tmp57 = tl.load(in_ptr9 + (x0 + 128*x4), None).to(tl.float32)
    tmp1 = tmp0.to(tl.float32)
    tmp3 = tmp1 * tmp2
    tmp5 = -0.5
    tmp6 = tmp4 * tmp5
    tmp7 = tmp2 * tmp2
    tmp8 = tmp7 * tmp2
    tmp9 = tmp6 * tmp8
    tmp10 = 0.0078125
    tmp11 = tmp9 * tmp10
    tmp13 = tmp12.to(tl.float32)
    tmp14 = 2.0
    tmp15 = tmp13 * tmp14
    tmp16 = tmp11 * tmp15
    tmp17 = tmp3 + tmp16
    tmp18 = tmp17.to(tl.float32)
    tmp20 = tmp18 * tmp19
    tmp22 = tmp21.to(tl.float32)
    tmp23 = tmp22 * tmp2
    tmp25 = tmp24.to(tl.float32)
    tmp26 = tmp25 * tmp14
    tmp27 = tmp11 * tmp26
    tmp28 = tmp23 + tmp27
    tmp29 = tmp28.to(tl.float32)
    tmp31 = tmp29 * tmp30
    tmp32 = tmp20 + tmp31
    tmp33 = -tmp30
    tmp34 = tmp18 * tmp33
    tmp35 = tmp29 * tmp19
    tmp36 = tmp34 + tmp35
    tmp38 = tmp37.to(tl.float32)
    tmp40 = tmp38 * tmp39
    tmp42 = tmp41 * tmp5
    tmp43 = tmp39 * tmp39
    tmp44 = tmp43 * tmp39
    tmp45 = tmp42 * tmp44
    tmp46 = tmp45 * tmp10
    tmp48 = tmp47.to(tl.float32)
    tmp49 = tmp48 * tmp14
    tmp50 = tmp46 * tmp49
    tmp51 = tmp40 + tmp50
    tmp52 = tmp51.to(tl.float32)
    tmp53 = tmp52 * tmp19
    tmp55 = tmp54.to(tl.float32)
    tmp56 = tmp55 * tmp39
    tmp58 = tmp57.to(tl.float32)
    tmp59 = tmp58 * tmp14
    tmp60 = tmp46 * tmp59
    tmp61 = tmp56 + tmp60
    tmp62 = tmp61.to(tl.float32)
    tmp63 = tmp62 * tmp30
    tmp64 = tmp53 + tmp63
    tmp65 = tmp52 * tmp33
    tmp66 = tmp62 * tmp19
    tmp67 = tmp65 + tmp66
    tl.store(out_ptr0 + (x5), tmp32, None)
    tl.store(out_ptr1 + (x5), tmp36, None)
    tl.store(out_ptr2 + (x5), tmp64, None)
    tl.store(out_ptr3 + (x5), tmp67, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/wx/cwx653h7sqcktmc2lrj5w3kre4ladoh2qjelzkwfzey7lmp6qod6.py
# Topologically Sorted Source Nodes: [loss, sigmoid_2], Original ATen: [aten.nll_loss_forward, aten.sigmoid, aten.mul, aten.sum, aten.sigmoid_backward, aten.embedding_dense_backward]
# Source node to ATen node mapping:
#   loss => full_default_1
#   sigmoid_2 => sigmoid_2
# Graph fragment:
#   %full_default_1 : [num_users=5] = call_function[target=torch.ops.aten.full.default](args = ([], 0.0), kwargs = {dtype: torch.float32, layout: torch.strided, device: cuda:0, pin_memory: False})
#   %sigmoid_2 : [num_users=2] = call_function[target=torch.ops.aten.sigmoid.default](args = (%view_107,), kwargs = {})
#   %mul_133 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%squeeze_1, %view_105), kwargs = {})
#   %sum_9 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mul_133, [3], True), kwargs = {dtype: torch.float32})
#   %mul_134 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%squeeze_3, 2), kwargs = {})
#   %convert_element_type_218 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul_134, torch.float32), kwargs = {})
#   %convert_element_type_219 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%sigmoid_2, torch.float32), kwargs = {})
#   %sub_4 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (1, %convert_element_type_219), kwargs = {})
#   %mul_135 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_219, %sub_4), kwargs = {})
#   %mul_136 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_218, %mul_135), kwargs = {})
#   %convert_element_type_220 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul_136, torch.bfloat16), kwargs = {})
#   %convert_element_type_243 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%view_135, torch.float32), kwargs = {})
#   %where_5 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%unsqueeze_17, %full_default_1, %convert_element_type_243), kwargs = {})
triton_per_fused_embedding_dense_backward_mul_nll_loss_forward_sigmoid_sigmoid_backward_sum_9 = async_compile.triton('triton_per_fused_embedding_dense_backward_mul_nll_loss_forward_sigmoid_sigmoid_backward_sum_9', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 131072, 'r': 128},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*i64', 'in_ptr3': '*bf16', 'out_ptr1': '*fp32', 'out_ptr2': '*bf16', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused_embedding_dense_backward_mul_nll_loss_forward_sigmoid_sigmoid_backward_sum_9', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 5, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused_embedding_dense_backward_mul_nll_loss_forward_sigmoid_sigmoid_backward_sum_9(in_ptr0, in_ptr1, in_ptr2, in_ptr3, out_ptr1, out_ptr2, xnumel, rnumel, XBLOCK : tl.constexpr):
    xnumel = 98304
    rnumel = 128
    RBLOCK: tl.constexpr = 128
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:, None]
    xmask = tl.full([XBLOCK, RBLOCK], True, tl.int1)
    rindex = tl.arange(0, RBLOCK)[None, :]
    roffset = 0
    rmask = tl.full([XBLOCK, RBLOCK], True, tl.int1)
    r1 = rindex
    x0 = xindex
    x3 = xindex // 3
    tmp0 = tl.load(in_ptr0 + (r1 + 128*x0), None).to(tl.float32)
    tmp1 = tl.load(in_ptr1 + (r1 + 128*x0), None).to(tl.float32)
    tmp7 = tl.load(in_ptr2 + (x3), None, eviction_policy='evict_last')
    tmp10 = tl.load(in_ptr3 + (x0), None).to(tl.float32)
    tmp21 = tl.load(in_ptr3 + (x0), None, eviction_policy='evict_last').to(tl.float32)
    tmp2 = tmp0 * tmp1
    tmp3 = tmp2.to(tl.float32)
    tmp4 = tl.broadcast_to(tmp3, [XBLOCK, RBLOCK])
    tmp6 = tl.sum(tmp4, 1)[:, None]
    tmp8 = tl.full([1, 1], -1, tl.int64)
    tmp9 = tmp7 == tmp8
    tmp11 = tl.sigmoid(tmp10)
    tmp12 = 2.0
    tmp13 = tmp11 * tmp12
    tmp14 = tmp0 * tmp13
    tmp15 = tmp14.to(tl.float32)
    tmp16 = 0.0
    tmp17 = tl.where(tmp9, tmp16, tmp15)
    tmp18 = tmp6.to(tl.float32)
    tmp19 = tmp18 * tmp12
    tmp20 = tmp19.to(tl.float32)
    tmp22 = tl.sigmoid(tmp21)
    tmp23 = tmp22.to(tl.float32)
    tmp24 = 1.0
    tmp25 = tmp24 - tmp23
    tmp26 = tmp23 * tmp25
    tmp27 = tmp20 * tmp26
    tmp28 = tmp27.to(tl.float32)
    tl.store(out_ptr1 + (r1 + 128*x0), tmp17, None)
    tl.store(out_ptr2 + (x0), tmp28, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/k5/ck5nbvqxjmjkdeuklusvg5sxqfzwiuskpsjik5jcw7m4eb7kraw3.py
# Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
# Source node to ATen node mapping:
# Graph fragment:
#   %convert_element_type_225 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mm_48, torch.float32), kwargs = {})
triton_poi_fused__to_copy_10 = async_compile.triton('triton_poi_fused__to_copy_10', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.pointwise(
    size_hints={'x': 128}, 
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*bf16', 'out_ptr0': '*fp32', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused__to_copy_10', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 1, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused__to_copy_10(in_ptr0, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 96
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = xindex < xnumel
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (x0), xmask).to(tl.float32)
    tmp1 = tmp0.to(tl.float32)
    tl.store(out_ptr0 + (x0), tmp1, xmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/fd/cfdl3f5aic23qj55fcde74phmnkqecj2a6f37muqfnszg4tah7px.py
# Topologically Sorted Source Nodes: [], Original ATen: [aten.slice_backward, aten.add]
# Source node to ATen node mapping:
# Graph fragment:
#   %full_default_6 : [num_users=24] = call_function[target=torch.ops.aten.full.default](args = ([16, 2048, 3, 128], 0), kwargs = {dtype: torch.bfloat16, layout: torch.strided, device: cuda:0, pin_memory: False})
#   %slice_scatter_default : [num_users=1] = call_function[target=torch.ops.aten.slice_scatter.default](args = (%full_default_6, %add_76, 3, 64, 9223372036854775807), kwargs = {})
#   %slice_scatter_default_1 : [num_users=1] = call_function[target=torch.ops.aten.slice_scatter.default](args = (%full_default_6, %add_77, 3, 0, 64), kwargs = {})
#   %add_78 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%slice_scatter_default, %slice_scatter_default_1), kwargs = {})
triton_poi_fused_add_slice_backward_11 = async_compile.triton('triton_poi_fused_add_slice_backward_11', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.pointwise(
    size_hints={'x': 16777216}, 
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'out_ptr0': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_add_slice_backward_11', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 2, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_add_slice_backward_11(in_ptr0, in_ptr1, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 12582912
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = (xindex % 128)
    x1 = xindex // 128
    x2 = xindex
    tmp0 = x0
    tmp1 = tl.full([1], 64, tl.int64)
    tmp2 = tmp0 >= tmp1
    tmp3 = tl.load(in_ptr0 + ((-64) + x0 + 64*x1), tmp2, other=0.0).to(tl.float32)
    tmp4 = 0.0
    tmp5 = tl.where(tmp2, tmp3, tmp4)
    tmp6 = tmp0 < tmp1
    tmp7 = tl.load(in_ptr1 + (x0 + 64*x1), tmp6, other=0.0).to(tl.float32)
    tmp8 = tl.where(tmp6, tmp7, tmp4)
    tmp9 = tmp5 + tmp8
    tl.store(out_ptr0 + (x2), tmp9, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/go/cgo74odqsxxqggqno2mu5xrhu7o7svio2ifi5q4isrquq6q4ff4t.py
# Topologically Sorted Source Nodes: [rms_norm_21], Original ATen: [aten.slice_backward, aten.add, aten._to_copy, aten.mul, aten.sum, aten.div, aten.pow]
# Source node to ATen node mapping:
#   rms_norm_21 => convert_element_type_148
# Graph fragment:
#   %full_default_10 : [num_users=3] = call_function[target=torch.ops.aten.full.default](args = ([16, 2048, 384], 0), kwargs = {dtype: torch.bfloat16, layout: torch.strided, device: cuda:0, pin_memory: False})
#   %slice_scatter_default_4 : [num_users=1] = call_function[target=torch.ops.aten.slice_scatter.default](args = (%full_default_10, %view_134, 2, 0, 32), kwargs = {})
#   %add_82 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%slice_scatter_default_4, %view_138), kwargs = {})
#   %add_83 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_82, %view_141), kwargs = {})
#   %add_84 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_83, %view_144), kwargs = {})
#   %convert_element_type_241 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_84, torch.float32), kwargs = {})
#   %convert_element_type_148 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_58, torch.float32), kwargs = {})
#   %mul_137 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_241, %convert_element_type_148), kwargs = {})
#   %mul_138 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_241, %rsqrt_21), kwargs = {})
#   %sum_10 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mul_137, [2], True), kwargs = {dtype: torch.float32})
#   %div_8 : [num_users=1] = call_function[target=torch.ops.aten.div.Scalar](args = (%expand_16, 384), kwargs = {})
#   %pow_43 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_148, 1.0), kwargs = {})
#   %mul_141 : [num_users=1] = call_function[target=torch.ops.aten.mul.Scalar](args = (%pow_43, 2.0), kwargs = {})
#   %mul_142 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%div_8, %mul_141), kwargs = {})
#   %add_85 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_138, %mul_142), kwargs = {})
#   %convert_element_type_242 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_85, torch.bfloat16), kwargs = {})
#   %add_86 : [num_users=4] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_73, %convert_element_type_242), kwargs = {})
#   %mul_145 : [num_users=2] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_86, %select_10), kwargs = {})
triton_red_fused__to_copy_add_div_mul_pow_slice_backward_sum_12 = async_compile.triton('triton_red_fused__to_copy_add_div_mul_pow_slice_backward_sum_12', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.reduction(
    size_hints={'x': 32768, 'r': 512},
    reduction_hint=ReductionHint.DEFAULT,
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'in_ptr3': '*bf16', 'in_ptr4': '*fp32', 'in_ptr5': '*bf16', 'in_ptr6': '*fp32', 'out_ptr1': '*bf16', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_red_fused__to_copy_add_div_mul_pow_slice_backward_sum_12', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 13, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_red_fused__to_copy_add_div_mul_pow_slice_backward_sum_12(in_out_ptr0, in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, in_ptr5, in_ptr6, out_ptr1, xnumel, rnumel, XBLOCK : tl.constexpr, RBLOCK : tl.constexpr):
    xnumel = 32768
    rnumel = 384
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:, None]
    xmask = tl.full([XBLOCK, RBLOCK], True, tl.int1)
    rbase = tl.arange(0, RBLOCK)[None, :]
    x0 = xindex
    _tmp17 = tl.full([XBLOCK, RBLOCK], 0, tl.float32)
    for roffset in range(0, rnumel, RBLOCK):
        rindex = roffset + rbase
        rmask = rindex < rnumel
        r1 = rindex
        tmp6 = tl.load(in_out_ptr0 + (r1 + 384*x0), rmask, eviction_policy='evict_last', other=0.0).to(tl.float32)
        tmp8 = tl.load(in_ptr1 + (r1 + 384*x0), rmask, eviction_policy='evict_last', other=0.0).to(tl.float32)
        tmp10 = tl.load(in_ptr2 + (r1 + 384*x0), rmask, eviction_policy='evict_last', other=0.0).to(tl.float32)
        tmp13 = tl.load(in_ptr3 + (r1 + 384*x0), rmask, eviction_policy='evict_last', other=0.0).to(tl.float32)
        tmp0 = r1
        tmp1 = tl.full([1, 1], 32, tl.int64)
        tmp2 = tmp0 < tmp1
        tmp3 = tl.load(in_ptr0 + (r1 + 32*x0), rmask & tmp2, eviction_policy='evict_last', other=0.0).to(tl.float32)
        tmp4 = 0.0
        tmp5 = tl.where(tmp2, tmp3, tmp4)
        tmp7 = tmp5 + tmp6
        tmp9 = tmp7 + tmp8
        tmp11 = tmp9 + tmp10
        tmp12 = tmp11.to(tl.float32)
        tmp14 = tmp13.to(tl.float32)
        tmp15 = tmp12 * tmp14
        tmp16 = tl.broadcast_to(tmp15, [XBLOCK, RBLOCK])
        tmp18 = _tmp17 + tmp16
        _tmp17 = tl.where(rmask, tmp18, _tmp17)
    tmp17 = tl.sum(_tmp17, 1)[:, None]
    tmp32 = tl.load(in_ptr4 + (x0), None, eviction_policy='evict_last')
    tmp50 = tl.load(in_ptr6 + (5))
    tmp51 = tl.broadcast_to(tmp50, [XBLOCK, RBLOCK])
    for roffset in range(0, rnumel, RBLOCK):
        rindex = roffset + rbase
        rmask = rindex < rnumel
        r1 = rindex
        tmp25 = tl.load(in_out_ptr0 + (r1 + 384*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp27 = tl.load(in_ptr1 + (r1 + 384*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp29 = tl.load(in_ptr2 + (r1 + 384*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp41 = tl.load(in_ptr3 + (r1 + 384*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp48 = tl.load(in_ptr5 + (r1 + 384*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp19 = r1
        tmp20 = tl.full([1, 1], 32, tl.int64)
        tmp21 = tmp19 < tmp20
        tmp22 = tl.load(in_ptr0 + (r1 + 32*x0), rmask & tmp21, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp23 = 0.0
        tmp24 = tl.where(tmp21, tmp22, tmp23)
        tmp26 = tmp24 + tmp25
        tmp28 = tmp26 + tmp27
        tmp30 = tmp28 + tmp29
        tmp31 = tmp30.to(tl.float32)
        tmp33 = tmp31 * tmp32
        tmp34 = -0.5
        tmp35 = tmp17 * tmp34
        tmp36 = tmp32 * tmp32
        tmp37 = tmp36 * tmp32
        tmp38 = tmp35 * tmp37
        tmp39 = 0.0026041666666666665
        tmp40 = tmp38 * tmp39
        tmp42 = tmp41.to(tl.float32)
        tmp43 = 2.0
        tmp44 = tmp42 * tmp43
        tmp45 = tmp40 * tmp44
        tmp46 = tmp33 + tmp45
        tmp47 = tmp46.to(tl.float32)
        tmp49 = tmp48 + tmp47
        tmp52 = tmp51.to(tl.float32)
        tmp53 = tmp49 * tmp52
        tl.store(in_out_ptr0 + (r1 + 384*x0), tmp47, rmask)
        tl.store(out_ptr1 + (r1 + 384*x0), tmp53, rmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/ru/cru7hkxhuxjcdqzilw4chair45tdnw4sczjbzngrcuy2txzpfi5c.py
# Topologically Sorted Source Nodes: [loss], Original ATen: [aten.nll_loss_forward, aten.embedding_dense_backward]
# Source node to ATen node mapping:
#   loss => full_default_1
# Graph fragment:
#   %full_default_1 : [num_users=5] = call_function[target=torch.ops.aten.full.default](args = ([], 0.0), kwargs = {dtype: torch.float32, layout: torch.strided, device: cuda:0, pin_memory: False})
#   %convert_element_type_243 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%view_135, torch.float32), kwargs = {})
#   %where_5 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%unsqueeze_17, %full_default_1, %convert_element_type_243), kwargs = {})
#   %full_default_12 : [num_users=4] = call_function[target=torch.ops.aten.full.default](args = ([8192, 384], 0), kwargs = {dtype: torch.float32, layout: torch.strided, device: cuda:0, pin_memory: False})
#   %index_put : [num_users=1] = call_function[target=torch.ops.aten.index_put.default](args = (%full_default_12, [%primals_1], %where_5, True), kwargs = {})
triton_poi_fused_embedding_dense_backward_nll_loss_forward_13 = async_compile.triton('triton_poi_fused_embedding_dense_backward_nll_loss_forward_13', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.pointwise(
    size_hints={'x': 4194304}, 
    filename=__file__,
    triton_meta={'signature': {'out_ptr0': '*fp32', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_embedding_dense_backward_nll_loss_forward_13', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 0, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_embedding_dense_backward_nll_loss_forward_13(out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 3145728
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = xindex
    tmp0 = 0.0
    tl.store(out_ptr0 + (x0), tmp0, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/bx/cbxopwzqk7rpgoxq2khciacswvqrpyz6yjm4af4cqpckchffnwqo.py
# Topologically Sorted Source Nodes: [], Original ATen: [aten.embedding_dense_backward]
# Source node to ATen node mapping:
# Graph fragment:
#   %convert_element_type_244 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%index_put, torch.bfloat16), kwargs = {})
triton_poi_fused_embedding_dense_backward_14 = async_compile.triton('triton_poi_fused_embedding_dense_backward_14', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.pointwise(
    size_hints={'x': 4194304}, 
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*fp32', 'out_ptr0': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_embedding_dense_backward_14', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 1, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_embedding_dense_backward_14(in_ptr0, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 3145728
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (x0), None)
    tmp1 = tmp0.to(tl.float32)
    tl.store(out_ptr0 + (x0), tmp1, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/ep/cepsnnlovhv4bhdqwwkjvw4v7scrdgok6e3t4xgdhduoxlqaumiw.py
# Topologically Sorted Source Nodes: [rms_norm_20], Original ATen: [aten._to_copy, aten.mul, aten.sum, aten.div, aten.pow, aten.add]
# Source node to ATen node mapping:
#   rms_norm_20 => convert_element_type_138
# Graph fragment:
#   %convert_element_type_257 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%view_148, torch.float32), kwargs = {})
#   %convert_element_type_138 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_55, torch.float32), kwargs = {})
#   %mul_149 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_257, %convert_element_type_138), kwargs = {})
#   %mul_150 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_257, %rsqrt_20), kwargs = {})
#   %sum_13 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mul_149, [2], True), kwargs = {dtype: torch.float32})
#   %div_9 : [num_users=1] = call_function[target=torch.ops.aten.div.Scalar](args = (%expand_17, 384), kwargs = {})
#   %pow_46 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_138, 1.0), kwargs = {})
#   %mul_153 : [num_users=1] = call_function[target=torch.ops.aten.mul.Scalar](args = (%pow_46, 2.0), kwargs = {})
#   %mul_154 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%div_9, %mul_153), kwargs = {})
#   %add_87 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_150, %mul_154), kwargs = {})
#   %convert_element_type_258 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_87, torch.bfloat16), kwargs = {})
#   %add_88 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_145, %convert_element_type_258), kwargs = {})
triton_per_fused__to_copy_add_div_mul_pow_sum_15 = async_compile.triton('triton_per_fused__to_copy_add_div_mul_pow_sum_15', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 32768, 'r': 512},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_div_mul_pow_sum_15', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': True, 'num_load': 4, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_div_mul_pow_sum_15(in_out_ptr0, in_ptr0, in_ptr1, in_ptr2, xnumel, rnumel):
    xnumel = 32768
    XBLOCK: tl.constexpr = 1
    rnumel = 384
    RBLOCK: tl.constexpr = 512
    xoffset = tl.program_id(0) * XBLOCK
    xindex = tl.full([1], xoffset, tl.int32)
    xmask = tl.full([RBLOCK], True, tl.int1)
    rindex = tl.arange(0, RBLOCK)[:]
    roffset = 0
    rmask = rindex < rnumel
    r1 = rindex
    x0 = xindex
    tmp0 = tl.load(in_out_ptr0 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp2 = tl.load(in_ptr0 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp9 = tl.load(in_ptr1 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp10 = tl.load(in_ptr2 + (x0), None, eviction_policy='evict_last')
    tmp1 = tmp0.to(tl.float32)
    tmp3 = tmp2.to(tl.float32)
    tmp4 = tmp1 * tmp3
    tmp5 = tl.broadcast_to(tmp4, [RBLOCK])
    tmp7 = tl.where(rmask, tmp5, 0)
    tmp8 = triton_helpers.promote_to_tensor(tl.sum(tmp7, 0))
    tmp11 = tmp1 * tmp10
    tmp12 = -0.5
    tmp13 = tmp8 * tmp12
    tmp14 = tmp10 * tmp10
    tmp15 = tmp14 * tmp10
    tmp16 = tmp13 * tmp15
    tmp17 = 0.0026041666666666665
    tmp18 = tmp16 * tmp17
    tmp19 = 2.0
    tmp20 = tmp3 * tmp19
    tmp21 = tmp18 * tmp20
    tmp22 = tmp11 + tmp21
    tmp23 = tmp22.to(tl.float32)
    tmp24 = tmp9 + tmp23
    tl.store(in_out_ptr0 + (r1 + 384*x0), tmp24, rmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/up/cupmrpya2rnmtaqoh2zrb24hrxccqsmpwyosped6nhwjkrzalzk7.py
# Topologically Sorted Source Nodes: [x_1, rms_norm_17], Original ATen: [aten.add, aten._to_copy, aten.mul, aten.sum, aten.div, aten.pow, aten.view]
# Source node to ATen node mapping:
#   rms_norm_17 => convert_element_type_120
#   x_1 => convert_element_type, convert_element_type_1, mul
# Graph fragment:
#   %add_86 : [num_users=4] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_73, %convert_element_type_242), kwargs = {})
#   %convert_element_type : [num_users=3] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%embedding, torch.float32), kwargs = {})
#   %mul : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type, %rsqrt), kwargs = {})
#   %convert_element_type_1 : [num_users=8] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul, torch.bfloat16), kwargs = {})
#   %mul_144 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_86, %convert_element_type_1), kwargs = {})
#   %sum_11 : [num_users=1] = call_function[target=torch.ops.aten.sum.default](args = (%mul_144,), kwargs = {dtype: torch.float32})
#   %mul_146 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_86, %add_57), kwargs = {})
#   %sum_12 : [num_users=1] = call_function[target=torch.ops.aten.sum.default](args = (%mul_146,), kwargs = {dtype: torch.float32})
#   %add_97 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%view_156, %view_159), kwargs = {})
#   %add_98 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_97, %view_162), kwargs = {})
#   %convert_element_type_283 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_98, torch.float32), kwargs = {})
#   %convert_element_type_120 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_47, torch.float32), kwargs = {})
#   %mul_175 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_283, %convert_element_type_120), kwargs = {})
#   %mul_176 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_283, %rsqrt_17), kwargs = {})
#   %sum_16 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mul_175, [2], True), kwargs = {dtype: torch.float32})
#   %div_12 : [num_users=1] = call_function[target=torch.ops.aten.div.Scalar](args = (%expand_20, 384), kwargs = {})
#   %pow_52 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_120, 1.0), kwargs = {})
#   %mul_179 : [num_users=1] = call_function[target=torch.ops.aten.mul.Scalar](args = (%pow_52, 2.0), kwargs = {})
#   %mul_180 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%div_12, %mul_179), kwargs = {})
#   %add_99 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_176, %mul_180), kwargs = {})
#   %convert_element_type_284 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_99, torch.bfloat16), kwargs = {})
#   %add_100 : [num_users=4] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_88, %convert_element_type_284), kwargs = {})
#   %mul_182 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_100, %convert_element_type_1), kwargs = {})
#   %sum_17 : [num_users=1] = call_function[target=torch.ops.aten.sum.default](args = (%mul_182,), kwargs = {dtype: torch.float32})
#   %mul_183 : [num_users=2] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_100, %select_8), kwargs = {})
#   %mul_184 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_100, %add_46), kwargs = {})
#   %sum_18 : [num_users=1] = call_function[target=torch.ops.aten.sum.default](args = (%mul_184,), kwargs = {dtype: torch.float32})
#   %view_163 : [num_users=2] = call_function[target=torch.ops.aten.reshape.default](args = (%mul_183, [32768, 384]), kwargs = {})
triton_per_fused__to_copy_add_div_mul_pow_sum_view_16 = async_compile.triton('triton_per_fused__to_copy_add_div_mul_pow_sum_view_16', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 32768, 'r': 512},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'in_ptr3': '*bf16', 'in_ptr4': '*fp32', 'in_ptr5': '*fp32', 'in_ptr6': '*bf16', 'in_ptr7': '*bf16', 'in_ptr8': '*bf16', 'in_ptr9': '*fp32', 'in_ptr10': '*bf16', 'in_ptr11': '*bf16', 'out_ptr1': '*bf16', 'out_ptr2': '*fp32', 'out_ptr3': '*fp32', 'out_ptr4': '*fp32', 'out_ptr5': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_div_mul_pow_sum_view_16', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': True, 'num_load': 13, 'num_reduction': 5, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_div_mul_pow_sum_view_16(in_out_ptr0, in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, in_ptr5, in_ptr6, in_ptr7, in_ptr8, in_ptr9, in_ptr10, in_ptr11, out_ptr1, out_ptr2, out_ptr3, out_ptr4, out_ptr5, xnumel, rnumel):
    xnumel = 32768
    XBLOCK: tl.constexpr = 1
    rnumel = 384
    RBLOCK: tl.constexpr = 512
    xoffset = tl.program_id(0) * XBLOCK
    xindex = tl.full([1], xoffset, tl.int32)
    xmask = tl.full([RBLOCK], True, tl.int1)
    rindex = tl.arange(0, RBLOCK)[:]
    roffset = 0
    rmask = rindex < rnumel
    r1 = rindex
    x0 = xindex
    tmp0 = tl.load(in_out_ptr0 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp1 = tl.load(in_ptr0 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp3 = tl.load(in_ptr1 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp6 = tl.load(in_ptr2 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp13 = tl.load(in_ptr3 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp14 = tl.load(in_ptr4 + (x0), None, eviction_policy='evict_last')
    tmp29 = tl.load(in_ptr5 + (4))
    tmp30 = tl.broadcast_to(tmp29, [RBLOCK])
    tmp33 = tl.load(in_ptr6 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp34 = tl.load(in_ptr7 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp36 = tl.load(in_ptr8 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp38 = tl.load(in_ptr9 + (x0), None, eviction_policy='evict_last')
    tmp47 = tl.load(in_ptr10 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp60 = tl.load(in_ptr11 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp2 = tmp0 + tmp1
    tmp4 = tmp2 + tmp3
    tmp5 = tmp4.to(tl.float32)
    tmp7 = tmp6.to(tl.float32)
    tmp8 = tmp5 * tmp7
    tmp9 = tl.broadcast_to(tmp8, [RBLOCK])
    tmp11 = tl.where(rmask, tmp9, 0)
    tmp12 = triton_helpers.promote_to_tensor(tl.sum(tmp11, 0))
    tmp15 = tmp5 * tmp14
    tmp16 = -0.5
    tmp17 = tmp12 * tmp16
    tmp18 = tmp14 * tmp14
    tmp19 = tmp18 * tmp14
    tmp20 = tmp17 * tmp19
    tmp21 = 0.0026041666666666665
    tmp22 = tmp20 * tmp21
    tmp23 = 2.0
    tmp24 = tmp7 * tmp23
    tmp25 = tmp22 * tmp24
    tmp26 = tmp15 + tmp25
    tmp27 = tmp26.to(tl.float32)
    tmp28 = tmp13 + tmp27
    tmp31 = tmp30.to(tl.float32)
    tmp32 = tmp28 * tmp31
    tmp35 = tmp33 + tmp34
    tmp37 = tmp36.to(tl.float32)
    tmp39 = tmp37 * tmp38
    tmp40 = tmp39.to(tl.float32)
    tmp41 = tmp35 * tmp40
    tmp42 = tmp41.to(tl.float32)
    tmp43 = tl.broadcast_to(tmp42, [RBLOCK])
    tmp45 = tl.where(rmask, tmp43, 0)
    tmp46 = triton_helpers.promote_to_tensor(tl.sum(tmp45, 0))
    tmp48 = tmp35 * tmp47
    tmp49 = tmp48.to(tl.float32)
    tmp50 = tl.broadcast_to(tmp49, [RBLOCK])
    tmp52 = tl.where(rmask, tmp50, 0)
    tmp53 = triton_helpers.promote_to_tensor(tl.sum(tmp52, 0))
    tmp54 = tmp28 * tmp40
    tmp55 = tmp54.to(tl.float32)
    tmp56 = tl.broadcast_to(tmp55, [RBLOCK])
    tmp58 = tl.where(rmask, tmp56, 0)
    tmp59 = triton_helpers.promote_to_tensor(tl.sum(tmp58, 0))
    tmp61 = tmp28 * tmp60
    tmp62 = tmp61.to(tl.float32)
    tmp63 = tl.broadcast_to(tmp62, [RBLOCK])
    tmp65 = tl.where(rmask, tmp63, 0)
    tmp66 = triton_helpers.promote_to_tensor(tl.sum(tmp65, 0))
    tl.store(in_out_ptr0 + (r1 + 384*x0), tmp28, rmask)
    tl.store(out_ptr1 + (r1 + 384*x0), tmp32, rmask)
    tl.store(out_ptr2 + (x0), tmp46, None)
    tl.store(out_ptr3 + (x0), tmp53, None)
    tl.store(out_ptr4 + (x0), tmp59, None)
    tl.store(out_ptr5 + (x0), tmp66, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/zl/czl3qqfvuvjwws2f6oqbe4q3636z6zgpipxex4glu7ljea35gb32.py
# Topologically Sorted Source Nodes: [x_1], Original ATen: [aten.add, aten._to_copy, aten.mul, aten.sum]
# Source node to ATen node mapping:
#   x_1 => convert_element_type, convert_element_type_1, mul
# Graph fragment:
#   %add_86 : [num_users=4] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_73, %convert_element_type_242), kwargs = {})
#   %convert_element_type : [num_users=3] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%embedding, torch.float32), kwargs = {})
#   %mul : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type, %rsqrt), kwargs = {})
#   %convert_element_type_1 : [num_users=8] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul, torch.bfloat16), kwargs = {})
#   %mul_144 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_86, %convert_element_type_1), kwargs = {})
#   %sum_11 : [num_users=1] = call_function[target=torch.ops.aten.sum.default](args = (%mul_144,), kwargs = {dtype: torch.float32})
triton_red_fused__to_copy_add_mul_sum_17 = async_compile.triton('triton_red_fused__to_copy_add_mul_sum_17', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.reduction(
    size_hints={'x': 1, 'r': 32768},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*fp32', 'out_ptr0': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {'xnumel': 1}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 3), 'tt.equal_to': (2,)}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_red_fused__to_copy_add_mul_sum_17', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 1, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_red_fused__to_copy_add_mul_sum_17(in_ptr0, out_ptr0, xnumel, rnumel, XBLOCK : tl.constexpr, RBLOCK : tl.constexpr):
    xnumel = 1
    rnumel = 32768
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:, None]
    xmask = tl.full([XBLOCK, RBLOCK], True, tl.int1)
    rbase = tl.arange(0, RBLOCK)[None, :]
    _tmp2 = tl.full([XBLOCK, RBLOCK], 0, tl.float32)
    for roffset in range(0, rnumel, RBLOCK):
        rindex = roffset + rbase
        rmask = rindex < rnumel
        r0 = rindex
        tmp0 = tl.load(in_ptr0 + (r0), rmask, eviction_policy='evict_first', other=0.0)
        tmp1 = tl.broadcast_to(tmp0, [XBLOCK, RBLOCK])
        tmp3 = _tmp2 + tmp1
        _tmp2 = tl.where(rmask, tmp3, _tmp2)
    tmp2 = tl.sum(_tmp2, 1)[:, None]
    tl.store(out_ptr0 + (tl.full([XBLOCK, 1], 0, tl.int32)), tmp2, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/ul/culjdxc6v7gshoqdc4ugumr6yhwwx7ng5jy57qlcjp52g5w5wssn.py
# Topologically Sorted Source Nodes: [rms_norm_16], Original ATen: [aten.mul, aten._to_copy, aten.sum, aten.div, aten.pow, aten.add]
# Source node to ATen node mapping:
#   rms_norm_16 => convert_element_type_110
# Graph fragment:
#   %mul_183 : [num_users=2] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_100, %select_8), kwargs = {})
#   %convert_element_type_297 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%view_166, torch.float32), kwargs = {})
#   %convert_element_type_110 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_44, torch.float32), kwargs = {})
#   %mul_187 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_297, %convert_element_type_110), kwargs = {})
#   %mul_188 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_297, %rsqrt_16), kwargs = {})
#   %sum_19 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mul_187, [2], True), kwargs = {dtype: torch.float32})
#   %div_13 : [num_users=1] = call_function[target=torch.ops.aten.div.Scalar](args = (%expand_21, 384), kwargs = {})
#   %pow_55 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_110, 1.0), kwargs = {})
#   %mul_191 : [num_users=1] = call_function[target=torch.ops.aten.mul.Scalar](args = (%pow_55, 2.0), kwargs = {})
#   %mul_192 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%div_13, %mul_191), kwargs = {})
#   %add_104 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_188, %mul_192), kwargs = {})
#   %convert_element_type_298 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_104, torch.bfloat16), kwargs = {})
#   %add_105 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_183, %convert_element_type_298), kwargs = {})
triton_per_fused__to_copy_add_div_mul_pow_sum_18 = async_compile.triton('triton_per_fused__to_copy_add_div_mul_pow_sum_18', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 32768, 'r': 512},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*fp32', 'in_ptr3': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_div_mul_pow_sum_18', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': True, 'num_load': 5, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_div_mul_pow_sum_18(in_out_ptr0, in_ptr0, in_ptr1, in_ptr2, in_ptr3, xnumel, rnumel):
    xnumel = 32768
    XBLOCK: tl.constexpr = 1
    rnumel = 384
    RBLOCK: tl.constexpr = 512
    xoffset = tl.program_id(0) * XBLOCK
    xindex = tl.full([1], xoffset, tl.int32)
    xmask = tl.full([RBLOCK], True, tl.int1)
    rindex = tl.arange(0, RBLOCK)[:]
    roffset = 0
    rmask = rindex < rnumel
    r1 = rindex
    x0 = xindex
    tmp0 = tl.load(in_out_ptr0 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp2 = tl.load(in_ptr0 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp9 = tl.load(in_ptr1 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp10 = tl.load(in_ptr2 + (4))
    tmp11 = tl.broadcast_to(tmp10, [RBLOCK])
    tmp14 = tl.load(in_ptr3 + (x0), None, eviction_policy='evict_last')
    tmp1 = tmp0.to(tl.float32)
    tmp3 = tmp2.to(tl.float32)
    tmp4 = tmp1 * tmp3
    tmp5 = tl.broadcast_to(tmp4, [RBLOCK])
    tmp7 = tl.where(rmask, tmp5, 0)
    tmp8 = triton_helpers.promote_to_tensor(tl.sum(tmp7, 0))
    tmp12 = tmp11.to(tl.float32)
    tmp13 = tmp9 * tmp12
    tmp15 = tmp1 * tmp14
    tmp16 = -0.5
    tmp17 = tmp8 * tmp16
    tmp18 = tmp14 * tmp14
    tmp19 = tmp18 * tmp14
    tmp20 = tmp17 * tmp19
    tmp21 = 0.0026041666666666665
    tmp22 = tmp20 * tmp21
    tmp23 = 2.0
    tmp24 = tmp3 * tmp23
    tmp25 = tmp22 * tmp24
    tmp26 = tmp15 + tmp25
    tmp27 = tmp26.to(tl.float32)
    tmp28 = tmp13 + tmp27
    tl.store(in_out_ptr0 + (r1 + 384*x0), tmp28, rmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/ii/ciidf2i4jxxgwt72w3ejqqvpdv2vwtymscha7oitvthe3wzg2tr2.py
# Topologically Sorted Source Nodes: [rms_norm_13], Original ATen: [aten.slice_backward, aten.add, aten._to_copy, aten.mul, aten.sum, aten.div, aten.pow]
# Source node to ATen node mapping:
#   rms_norm_13 => convert_element_type_89
# Graph fragment:
#   %full_default_10 : [num_users=3] = call_function[target=torch.ops.aten.full.default](args = ([16, 2048, 384], 0), kwargs = {dtype: torch.bfloat16, layout: torch.strided, device: cuda:0, pin_memory: False})
#   %slice_scatter_default_13 : [num_users=1] = call_function[target=torch.ops.aten.slice_scatter.default](args = (%full_default_10, %view_173, 2, 0, 32), kwargs = {})
#   %add_114 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%slice_scatter_default_13, %view_177), kwargs = {})
#   %add_115 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_114, %view_180), kwargs = {})
#   %add_116 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_115, %view_183), kwargs = {})
#   %convert_element_type_332 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_116, torch.float32), kwargs = {})
#   %convert_element_type_89 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_35, torch.float32), kwargs = {})
#   %mul_218 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_332, %convert_element_type_89), kwargs = {})
#   %mul_219 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_332, %rsqrt_13), kwargs = {})
#   %sum_23 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mul_218, [2], True), kwargs = {dtype: torch.float32})
#   %div_16 : [num_users=1] = call_function[target=torch.ops.aten.div.Scalar](args = (%expand_24, 384), kwargs = {})
#   %pow_61 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_89, 1.0), kwargs = {})
#   %mul_222 : [num_users=1] = call_function[target=torch.ops.aten.mul.Scalar](args = (%pow_61, 2.0), kwargs = {})
#   %mul_223 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%div_16, %mul_222), kwargs = {})
#   %add_117 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_219, %mul_223), kwargs = {})
#   %convert_element_type_333 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_117, torch.bfloat16), kwargs = {})
#   %add_118 : [num_users=4] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_105, %convert_element_type_333), kwargs = {})
#   %mul_226 : [num_users=2] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_118, %select_6), kwargs = {})
triton_red_fused__to_copy_add_div_mul_pow_slice_backward_sum_19 = async_compile.triton('triton_red_fused__to_copy_add_div_mul_pow_slice_backward_sum_19', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.reduction(
    size_hints={'x': 32768, 'r': 512},
    reduction_hint=ReductionHint.DEFAULT,
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'in_ptr3': '*bf16', 'in_ptr4': '*fp32', 'in_ptr5': '*bf16', 'in_ptr6': '*fp32', 'out_ptr1': '*bf16', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_red_fused__to_copy_add_div_mul_pow_slice_backward_sum_19', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 13, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_red_fused__to_copy_add_div_mul_pow_slice_backward_sum_19(in_out_ptr0, in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, in_ptr5, in_ptr6, out_ptr1, xnumel, rnumel, XBLOCK : tl.constexpr, RBLOCK : tl.constexpr):
    xnumel = 32768
    rnumel = 384
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:, None]
    xmask = tl.full([XBLOCK, RBLOCK], True, tl.int1)
    rbase = tl.arange(0, RBLOCK)[None, :]
    x0 = xindex
    _tmp17 = tl.full([XBLOCK, RBLOCK], 0, tl.float32)
    for roffset in range(0, rnumel, RBLOCK):
        rindex = roffset + rbase
        rmask = rindex < rnumel
        r1 = rindex
        tmp6 = tl.load(in_out_ptr0 + (r1 + 384*x0), rmask, eviction_policy='evict_last', other=0.0).to(tl.float32)
        tmp8 = tl.load(in_ptr1 + (r1 + 384*x0), rmask, eviction_policy='evict_last', other=0.0).to(tl.float32)
        tmp10 = tl.load(in_ptr2 + (r1 + 384*x0), rmask, eviction_policy='evict_last', other=0.0).to(tl.float32)
        tmp13 = tl.load(in_ptr3 + (r1 + 384*x0), rmask, eviction_policy='evict_last', other=0.0).to(tl.float32)
        tmp0 = r1
        tmp1 = tl.full([1, 1], 32, tl.int64)
        tmp2 = tmp0 < tmp1
        tmp3 = tl.load(in_ptr0 + (r1 + 32*x0), rmask & tmp2, eviction_policy='evict_last', other=0.0).to(tl.float32)
        tmp4 = 0.0
        tmp5 = tl.where(tmp2, tmp3, tmp4)
        tmp7 = tmp5 + tmp6
        tmp9 = tmp7 + tmp8
        tmp11 = tmp9 + tmp10
        tmp12 = tmp11.to(tl.float32)
        tmp14 = tmp13.to(tl.float32)
        tmp15 = tmp12 * tmp14
        tmp16 = tl.broadcast_to(tmp15, [XBLOCK, RBLOCK])
        tmp18 = _tmp17 + tmp16
        _tmp17 = tl.where(rmask, tmp18, _tmp17)
    tmp17 = tl.sum(_tmp17, 1)[:, None]
    tmp32 = tl.load(in_ptr4 + (x0), None, eviction_policy='evict_last')
    tmp50 = tl.load(in_ptr6 + (3))
    tmp51 = tl.broadcast_to(tmp50, [XBLOCK, RBLOCK])
    for roffset in range(0, rnumel, RBLOCK):
        rindex = roffset + rbase
        rmask = rindex < rnumel
        r1 = rindex
        tmp25 = tl.load(in_out_ptr0 + (r1 + 384*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp27 = tl.load(in_ptr1 + (r1 + 384*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp29 = tl.load(in_ptr2 + (r1 + 384*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp41 = tl.load(in_ptr3 + (r1 + 384*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp48 = tl.load(in_ptr5 + (r1 + 384*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp19 = r1
        tmp20 = tl.full([1, 1], 32, tl.int64)
        tmp21 = tmp19 < tmp20
        tmp22 = tl.load(in_ptr0 + (r1 + 32*x0), rmask & tmp21, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp23 = 0.0
        tmp24 = tl.where(tmp21, tmp22, tmp23)
        tmp26 = tmp24 + tmp25
        tmp28 = tmp26 + tmp27
        tmp30 = tmp28 + tmp29
        tmp31 = tmp30.to(tl.float32)
        tmp33 = tmp31 * tmp32
        tmp34 = -0.5
        tmp35 = tmp17 * tmp34
        tmp36 = tmp32 * tmp32
        tmp37 = tmp36 * tmp32
        tmp38 = tmp35 * tmp37
        tmp39 = 0.0026041666666666665
        tmp40 = tmp38 * tmp39
        tmp42 = tmp41.to(tl.float32)
        tmp43 = 2.0
        tmp44 = tmp42 * tmp43
        tmp45 = tmp40 * tmp44
        tmp46 = tmp33 + tmp45
        tmp47 = tmp46.to(tl.float32)
        tmp49 = tmp48 + tmp47
        tmp52 = tmp51.to(tl.float32)
        tmp53 = tmp49 * tmp52
        tl.store(in_out_ptr0 + (r1 + 384*x0), tmp47, rmask)
        tl.store(out_ptr1 + (r1 + 384*x0), tmp53, rmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/lz/clzfk7xvfqa36he2tqoafuym7w6yn6q623g6r5nkbb7lhky67ywi.py
# Topologically Sorted Source Nodes: [x_1, rms_norm_9], Original ATen: [aten.add, aten.mul, aten._to_copy, aten.sum, aten.div, aten.pow, aten.view]
# Source node to ATen node mapping:
#   rms_norm_9 => convert_element_type_61
#   x_1 => convert_element_type, convert_element_type_1, mul
# Graph fragment:
#   %add_86 : [num_users=4] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_73, %convert_element_type_242), kwargs = {})
#   %mul_143 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_86, %select_11), kwargs = {})
#   %convert_element_type : [num_users=3] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%embedding, torch.float32), kwargs = {})
#   %mul : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type, %rsqrt), kwargs = {})
#   %convert_element_type_1 : [num_users=8] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul, torch.bfloat16), kwargs = {})
#   %mul_181 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_100, %select_9), kwargs = {})
#   %add_101 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_143, %mul_181), kwargs = {})
#   %add_118 : [num_users=4] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_105, %convert_element_type_333), kwargs = {})
#   %mul_224 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_118, %select_7), kwargs = {})
#   %mul_225 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_118, %convert_element_type_1), kwargs = {})
#   %sum_24 : [num_users=1] = call_function[target=torch.ops.aten.sum.default](args = (%mul_225,), kwargs = {dtype: torch.float32})
#   %add_119 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_101, %mul_224), kwargs = {})
#   %mul_227 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_118, %add_34), kwargs = {})
#   %sum_25 : [num_users=1] = call_function[target=torch.ops.aten.sum.default](args = (%mul_227,), kwargs = {dtype: torch.float32})
#   %add_132 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%view_195, %view_198), kwargs = {})
#   %add_133 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_132, %view_201), kwargs = {})
#   %convert_element_type_374 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_133, torch.float32), kwargs = {})
#   %convert_element_type_61 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_24, torch.float32), kwargs = {})
#   %mul_256 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_374, %convert_element_type_61), kwargs = {})
#   %mul_257 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_374, %rsqrt_9), kwargs = {})
#   %sum_29 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mul_256, [2], True), kwargs = {dtype: torch.float32})
#   %div_20 : [num_users=1] = call_function[target=torch.ops.aten.div.Scalar](args = (%expand_28, 384), kwargs = {})
#   %pow_70 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_61, 1.0), kwargs = {})
#   %mul_260 : [num_users=1] = call_function[target=torch.ops.aten.mul.Scalar](args = (%pow_70, 2.0), kwargs = {})
#   %mul_261 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%div_20, %mul_260), kwargs = {})
#   %add_134 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_257, %mul_261), kwargs = {})
#   %convert_element_type_375 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_134, torch.bfloat16), kwargs = {})
#   %add_135 : [num_users=4] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_123, %convert_element_type_375), kwargs = {})
#   %mul_262 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_135, %select_5), kwargs = {})
#   %mul_263 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_135, %convert_element_type_1), kwargs = {})
#   %sum_30 : [num_users=1] = call_function[target=torch.ops.aten.sum.default](args = (%mul_263,), kwargs = {dtype: torch.float32})
#   %add_136 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_119, %mul_262), kwargs = {})
#   %mul_264 : [num_users=2] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_135, %select_4), kwargs = {})
#   %mul_265 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_135, %add_23), kwargs = {})
#   %sum_31 : [num_users=1] = call_function[target=torch.ops.aten.sum.default](args = (%mul_265,), kwargs = {dtype: torch.float32})
#   %view_202 : [num_users=2] = call_function[target=torch.ops.aten.reshape.default](args = (%mul_264, [32768, 384]), kwargs = {})
triton_per_fused__to_copy_add_div_mul_pow_sum_view_20 = async_compile.triton('triton_per_fused__to_copy_add_div_mul_pow_sum_view_20', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 32768, 'r': 512},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_out_ptr1': '*bf16', 'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'in_ptr3': '*bf16', 'in_ptr4': '*fp32', 'in_ptr5': '*bf16', 'in_ptr6': '*fp32', 'in_ptr7': '*bf16', 'in_ptr8': '*bf16', 'in_ptr9': '*bf16', 'in_ptr10': '*fp32', 'in_ptr11': '*bf16', 'in_ptr12': '*fp32', 'in_ptr13': '*bf16', 'in_ptr14': '*bf16', 'out_ptr1': '*bf16', 'out_ptr2': '*fp32', 'out_ptr3': '*fp32', 'out_ptr4': '*fp32', 'out_ptr5': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_div_mul_pow_sum_view_20', 'mutated_arg_names': ['in_out_ptr0', 'in_out_ptr1'], 'optimize_mem': True, 'no_x_dim': True, 'num_load': 20, 'num_reduction': 5, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_div_mul_pow_sum_view_20(in_out_ptr0, in_out_ptr1, in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, in_ptr5, in_ptr6, in_ptr7, in_ptr8, in_ptr9, in_ptr10, in_ptr11, in_ptr12, in_ptr13, in_ptr14, out_ptr1, out_ptr2, out_ptr3, out_ptr4, out_ptr5, xnumel, rnumel):
    xnumel = 32768
    XBLOCK: tl.constexpr = 1
    rnumel = 384
    RBLOCK: tl.constexpr = 512
    xoffset = tl.program_id(0) * XBLOCK
    xindex = tl.full([1], xoffset, tl.int32)
    xmask = tl.full([RBLOCK], True, tl.int1)
    rindex = tl.arange(0, RBLOCK)[:]
    roffset = 0
    rmask = rindex < rnumel
    r1 = rindex
    x0 = xindex
    tmp0 = tl.load(in_out_ptr0 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp1 = tl.load(in_ptr0 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp3 = tl.load(in_ptr1 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp6 = tl.load(in_ptr2 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp13 = tl.load(in_ptr3 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp14 = tl.load(in_ptr4 + (x0), None, eviction_policy='evict_last')
    tmp29 = tl.load(in_out_ptr1 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp30 = tl.load(in_ptr5 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp32 = tl.load(in_ptr6 + (5))
    tmp33 = tl.broadcast_to(tmp32, [RBLOCK])
    tmp36 = tl.load(in_ptr7 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp37 = tl.load(in_ptr6 + (4))
    tmp38 = tl.broadcast_to(tmp37, [RBLOCK])
    tmp42 = tl.load(in_ptr8 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp43 = tl.load(in_ptr9 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp45 = tl.load(in_ptr6 + (3))
    tmp46 = tl.broadcast_to(tmp45, [RBLOCK])
    tmp50 = tl.load(in_ptr6 + (2))
    tmp51 = tl.broadcast_to(tmp50, [RBLOCK])
    tmp55 = tl.load(in_ptr10 + (2))
    tmp56 = tl.broadcast_to(tmp55, [RBLOCK])
    tmp59 = tl.load(in_ptr11 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp61 = tl.load(in_ptr12 + (x0), None, eviction_policy='evict_last')
    tmp70 = tl.load(in_ptr13 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp83 = tl.load(in_ptr14 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp2 = tmp0 + tmp1
    tmp4 = tmp2 + tmp3
    tmp5 = tmp4.to(tl.float32)
    tmp7 = tmp6.to(tl.float32)
    tmp8 = tmp5 * tmp7
    tmp9 = tl.broadcast_to(tmp8, [RBLOCK])
    tmp11 = tl.where(rmask, tmp9, 0)
    tmp12 = triton_helpers.promote_to_tensor(tl.sum(tmp11, 0))
    tmp15 = tmp5 * tmp14
    tmp16 = -0.5
    tmp17 = tmp12 * tmp16
    tmp18 = tmp14 * tmp14
    tmp19 = tmp18 * tmp14
    tmp20 = tmp17 * tmp19
    tmp21 = 0.0026041666666666665
    tmp22 = tmp20 * tmp21
    tmp23 = 2.0
    tmp24 = tmp7 * tmp23
    tmp25 = tmp22 * tmp24
    tmp26 = tmp15 + tmp25
    tmp27 = tmp26.to(tl.float32)
    tmp28 = tmp13 + tmp27
    tmp31 = tmp29 + tmp30
    tmp34 = tmp33.to(tl.float32)
    tmp35 = tmp31 * tmp34
    tmp39 = tmp38.to(tl.float32)
    tmp40 = tmp36 * tmp39
    tmp41 = tmp35 + tmp40
    tmp44 = tmp42 + tmp43
    tmp47 = tmp46.to(tl.float32)
    tmp48 = tmp44 * tmp47
    tmp49 = tmp41 + tmp48
    tmp52 = tmp51.to(tl.float32)
    tmp53 = tmp28 * tmp52
    tmp54 = tmp49 + tmp53
    tmp57 = tmp56.to(tl.float32)
    tmp58 = tmp28 * tmp57
    tmp60 = tmp59.to(tl.float32)
    tmp62 = tmp60 * tmp61
    tmp63 = tmp62.to(tl.float32)
    tmp64 = tmp44 * tmp63
    tmp65 = tmp64.to(tl.float32)
    tmp66 = tl.broadcast_to(tmp65, [RBLOCK])
    tmp68 = tl.where(rmask, tmp66, 0)
    tmp69 = triton_helpers.promote_to_tensor(tl.sum(tmp68, 0))
    tmp71 = tmp44 * tmp70
    tmp72 = tmp71.to(tl.float32)
    tmp73 = tl.broadcast_to(tmp72, [RBLOCK])
    tmp75 = tl.where(rmask, tmp73, 0)
    tmp76 = triton_helpers.promote_to_tensor(tl.sum(tmp75, 0))
    tmp77 = tmp28 * tmp63
    tmp78 = tmp77.to(tl.float32)
    tmp79 = tl.broadcast_to(tmp78, [RBLOCK])
    tmp81 = tl.where(rmask, tmp79, 0)
    tmp82 = triton_helpers.promote_to_tensor(tl.sum(tmp81, 0))
    tmp84 = tmp28 * tmp83
    tmp85 = tmp84.to(tl.float32)
    tmp86 = tl.broadcast_to(tmp85, [RBLOCK])
    tmp88 = tl.where(rmask, tmp86, 0)
    tmp89 = triton_helpers.promote_to_tensor(tl.sum(tmp88, 0))
    tl.store(in_out_ptr0 + (r1 + 384*x0), tmp28, rmask)
    tl.store(in_out_ptr1 + (r1 + 384*x0), tmp54, rmask)
    tl.store(out_ptr1 + (r1 + 384*x0), tmp58, rmask)
    tl.store(out_ptr2 + (x0), tmp69, None)
    tl.store(out_ptr3 + (x0), tmp76, None)
    tl.store(out_ptr4 + (x0), tmp82, None)
    tl.store(out_ptr5 + (x0), tmp89, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/cf/ccfspbmmvirazglhqhicaeoxzok5gwhzku3mgk6we7of3pfvr3pq.py
# Topologically Sorted Source Nodes: [rms_norm_8], Original ATen: [aten.mul, aten._to_copy, aten.sum, aten.div, aten.pow, aten.add]
# Source node to ATen node mapping:
#   rms_norm_8 => convert_element_type_51
# Graph fragment:
#   %mul_264 : [num_users=2] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_135, %select_4), kwargs = {})
#   %convert_element_type_388 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%view_205, torch.float32), kwargs = {})
#   %convert_element_type_51 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_21, torch.float32), kwargs = {})
#   %mul_268 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_388, %convert_element_type_51), kwargs = {})
#   %mul_269 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_388, %rsqrt_8), kwargs = {})
#   %sum_32 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mul_268, [2], True), kwargs = {dtype: torch.float32})
#   %div_21 : [num_users=1] = call_function[target=torch.ops.aten.div.Scalar](args = (%expand_29, 384), kwargs = {})
#   %pow_73 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_51, 1.0), kwargs = {})
#   %mul_272 : [num_users=1] = call_function[target=torch.ops.aten.mul.Scalar](args = (%pow_73, 2.0), kwargs = {})
#   %mul_273 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%div_21, %mul_272), kwargs = {})
#   %add_139 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_269, %mul_273), kwargs = {})
#   %convert_element_type_389 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_139, torch.bfloat16), kwargs = {})
#   %add_140 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_264, %convert_element_type_389), kwargs = {})
triton_per_fused__to_copy_add_div_mul_pow_sum_21 = async_compile.triton('triton_per_fused__to_copy_add_div_mul_pow_sum_21', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 32768, 'r': 512},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*fp32', 'in_ptr3': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_div_mul_pow_sum_21', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': True, 'num_load': 5, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_div_mul_pow_sum_21(in_out_ptr0, in_ptr0, in_ptr1, in_ptr2, in_ptr3, xnumel, rnumel):
    xnumel = 32768
    XBLOCK: tl.constexpr = 1
    rnumel = 384
    RBLOCK: tl.constexpr = 512
    xoffset = tl.program_id(0) * XBLOCK
    xindex = tl.full([1], xoffset, tl.int32)
    xmask = tl.full([RBLOCK], True, tl.int1)
    rindex = tl.arange(0, RBLOCK)[:]
    roffset = 0
    rmask = rindex < rnumel
    r1 = rindex
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp2 = tl.load(in_ptr1 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp9 = tl.load(in_out_ptr0 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp10 = tl.load(in_ptr2 + (2))
    tmp11 = tl.broadcast_to(tmp10, [RBLOCK])
    tmp14 = tl.load(in_ptr3 + (x0), None, eviction_policy='evict_last')
    tmp1 = tmp0.to(tl.float32)
    tmp3 = tmp2.to(tl.float32)
    tmp4 = tmp1 * tmp3
    tmp5 = tl.broadcast_to(tmp4, [RBLOCK])
    tmp7 = tl.where(rmask, tmp5, 0)
    tmp8 = triton_helpers.promote_to_tensor(tl.sum(tmp7, 0))
    tmp12 = tmp11.to(tl.float32)
    tmp13 = tmp9 * tmp12
    tmp15 = tmp1 * tmp14
    tmp16 = -0.5
    tmp17 = tmp8 * tmp16
    tmp18 = tmp14 * tmp14
    tmp19 = tmp18 * tmp14
    tmp20 = tmp17 * tmp19
    tmp21 = 0.0026041666666666665
    tmp22 = tmp20 * tmp21
    tmp23 = 2.0
    tmp24 = tmp3 * tmp23
    tmp25 = tmp22 * tmp24
    tmp26 = tmp15 + tmp25
    tmp27 = tmp26.to(tl.float32)
    tmp28 = tmp13 + tmp27
    tl.store(in_out_ptr0 + (r1 + 384*x0), tmp28, rmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/sf/csfhpojxrpxed7raw4sytvrqsaqdjuvh57pzwpyqqwcw47hxo5dj.py
# Topologically Sorted Source Nodes: [sigmoid], Original ATen: [aten.sigmoid, aten.mul, aten.sum, aten.sigmoid_backward]
# Source node to ATen node mapping:
#   sigmoid => sigmoid
# Graph fragment:
#   %sigmoid : [num_users=2] = call_function[target=torch.ops.aten.sigmoid.default](args = (%view_29,), kwargs = {})
#   %mul_295 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%squeeze_11, %view_27), kwargs = {})
#   %sum_35 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mul_295, [3], True), kwargs = {dtype: torch.float32})
#   %mul_296 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%squeeze_13, 2), kwargs = {})
#   %convert_element_type_400 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul_296, torch.float32), kwargs = {})
#   %convert_element_type_401 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%sigmoid, torch.float32), kwargs = {})
#   %sub_6 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (1, %convert_element_type_401), kwargs = {})
#   %mul_297 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_401, %sub_6), kwargs = {})
#   %mul_298 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_400, %mul_297), kwargs = {})
#   %convert_element_type_402 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul_298, torch.bfloat16), kwargs = {})
triton_per_fused_mul_sigmoid_sigmoid_backward_sum_22 = async_compile.triton('triton_per_fused_mul_sigmoid_sigmoid_backward_sum_22', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 131072, 'r': 128},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'out_ptr1': '*bf16', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused_mul_sigmoid_sigmoid_backward_sum_22', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 3, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused_mul_sigmoid_sigmoid_backward_sum_22(in_ptr0, in_ptr1, in_ptr2, out_ptr1, xnumel, rnumel, XBLOCK : tl.constexpr):
    xnumel = 98304
    rnumel = 128
    RBLOCK: tl.constexpr = 128
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:, None]
    xmask = tl.full([XBLOCK, RBLOCK], True, tl.int1)
    rindex = tl.arange(0, RBLOCK)[None, :]
    roffset = 0
    rmask = tl.full([XBLOCK, RBLOCK], True, tl.int1)
    r1 = rindex
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (r1 + 128*x0), None).to(tl.float32)
    tmp1 = tl.load(in_ptr1 + (r1 + 128*x0), None).to(tl.float32)
    tmp11 = tl.load(in_ptr2 + (x0), None, eviction_policy='evict_last').to(tl.float32)
    tmp2 = tmp0 * tmp1
    tmp3 = tmp2.to(tl.float32)
    tmp4 = tl.broadcast_to(tmp3, [XBLOCK, RBLOCK])
    tmp6 = tl.sum(tmp4, 1)[:, None]
    tmp7 = tmp6.to(tl.float32)
    tmp8 = 2.0
    tmp9 = tmp7 * tmp8
    tmp10 = tmp9.to(tl.float32)
    tmp12 = tl.sigmoid(tmp11)
    tmp13 = tmp12.to(tl.float32)
    tmp14 = 1.0
    tmp15 = tmp14 - tmp13
    tmp16 = tmp13 * tmp15
    tmp17 = tmp10 * tmp16
    tmp18 = tmp17.to(tl.float32)
    tl.store(out_ptr1 + (x0), tmp18, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/xh/cxhfb7snxh33qcufrzu6rgi6lv76yz6qagpnopjpt7gp4hc45vr4.py
# Topologically Sorted Source Nodes: [rms_norm_5], Original ATen: [aten.slice_backward, aten.add, aten._to_copy, aten.mul, aten.sum, aten.div, aten.pow]
# Source node to ATen node mapping:
#   rms_norm_5 => convert_element_type_30
# Graph fragment:
#   %full_default_10 : [num_users=3] = call_function[target=torch.ops.aten.full.default](args = ([16, 2048, 384], 0), kwargs = {dtype: torch.bfloat16, layout: torch.strided, device: cuda:0, pin_memory: False})
#   %slice_scatter_default_22 : [num_users=1] = call_function[target=torch.ops.aten.slice_scatter.default](args = (%full_default_10, %view_212, 2, 0, 32), kwargs = {})
#   %add_149 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%slice_scatter_default_22, %view_216), kwargs = {})
#   %add_150 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_149, %view_219), kwargs = {})
#   %add_151 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_150, %view_222), kwargs = {})
#   %convert_element_type_423 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_151, torch.float32), kwargs = {})
#   %convert_element_type_30 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_12, torch.float32), kwargs = {})
#   %mul_299 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_423, %convert_element_type_30), kwargs = {})
#   %mul_300 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_423, %rsqrt_5), kwargs = {})
#   %sum_36 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mul_299, [2], True), kwargs = {dtype: torch.float32})
#   %div_24 : [num_users=1] = call_function[target=torch.ops.aten.div.Scalar](args = (%expand_32, 384), kwargs = {})
#   %pow_79 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_30, 1.0), kwargs = {})
#   %mul_303 : [num_users=1] = call_function[target=torch.ops.aten.mul.Scalar](args = (%pow_79, 2.0), kwargs = {})
#   %mul_304 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%div_24, %mul_303), kwargs = {})
#   %add_152 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_300, %mul_304), kwargs = {})
#   %convert_element_type_424 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_152, torch.bfloat16), kwargs = {})
#   %add_153 : [num_users=4] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_140, %convert_element_type_424), kwargs = {})
#   %mul_307 : [num_users=2] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_153, %select_2), kwargs = {})
triton_red_fused__to_copy_add_div_mul_pow_slice_backward_sum_23 = async_compile.triton('triton_red_fused__to_copy_add_div_mul_pow_slice_backward_sum_23', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.reduction(
    size_hints={'x': 32768, 'r': 512},
    reduction_hint=ReductionHint.DEFAULT,
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'in_ptr3': '*bf16', 'in_ptr4': '*fp32', 'in_ptr5': '*bf16', 'in_ptr6': '*fp32', 'out_ptr1': '*bf16', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_red_fused__to_copy_add_div_mul_pow_slice_backward_sum_23', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 13, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_red_fused__to_copy_add_div_mul_pow_slice_backward_sum_23(in_out_ptr0, in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, in_ptr5, in_ptr6, out_ptr1, xnumel, rnumel, XBLOCK : tl.constexpr, RBLOCK : tl.constexpr):
    xnumel = 32768
    rnumel = 384
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:, None]
    xmask = tl.full([XBLOCK, RBLOCK], True, tl.int1)
    rbase = tl.arange(0, RBLOCK)[None, :]
    x0 = xindex
    _tmp17 = tl.full([XBLOCK, RBLOCK], 0, tl.float32)
    for roffset in range(0, rnumel, RBLOCK):
        rindex = roffset + rbase
        rmask = rindex < rnumel
        r1 = rindex
        tmp6 = tl.load(in_out_ptr0 + (r1 + 384*x0), rmask, eviction_policy='evict_last', other=0.0).to(tl.float32)
        tmp8 = tl.load(in_ptr1 + (r1 + 384*x0), rmask, eviction_policy='evict_last', other=0.0).to(tl.float32)
        tmp10 = tl.load(in_ptr2 + (r1 + 384*x0), rmask, eviction_policy='evict_last', other=0.0).to(tl.float32)
        tmp13 = tl.load(in_ptr3 + (r1 + 384*x0), rmask, eviction_policy='evict_last', other=0.0).to(tl.float32)
        tmp0 = r1
        tmp1 = tl.full([1, 1], 32, tl.int64)
        tmp2 = tmp0 < tmp1
        tmp3 = tl.load(in_ptr0 + (r1 + 32*x0), rmask & tmp2, eviction_policy='evict_last', other=0.0).to(tl.float32)
        tmp4 = 0.0
        tmp5 = tl.where(tmp2, tmp3, tmp4)
        tmp7 = tmp5 + tmp6
        tmp9 = tmp7 + tmp8
        tmp11 = tmp9 + tmp10
        tmp12 = tmp11.to(tl.float32)
        tmp14 = tmp13.to(tl.float32)
        tmp15 = tmp12 * tmp14
        tmp16 = tl.broadcast_to(tmp15, [XBLOCK, RBLOCK])
        tmp18 = _tmp17 + tmp16
        _tmp17 = tl.where(rmask, tmp18, _tmp17)
    tmp17 = tl.sum(_tmp17, 1)[:, None]
    tmp32 = tl.load(in_ptr4 + (x0), None, eviction_policy='evict_last')
    tmp50 = tl.load(in_ptr6 + (1))
    tmp51 = tl.broadcast_to(tmp50, [XBLOCK, RBLOCK])
    for roffset in range(0, rnumel, RBLOCK):
        rindex = roffset + rbase
        rmask = rindex < rnumel
        r1 = rindex
        tmp25 = tl.load(in_out_ptr0 + (r1 + 384*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp27 = tl.load(in_ptr1 + (r1 + 384*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp29 = tl.load(in_ptr2 + (r1 + 384*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp41 = tl.load(in_ptr3 + (r1 + 384*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp48 = tl.load(in_ptr5 + (r1 + 384*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp19 = r1
        tmp20 = tl.full([1, 1], 32, tl.int64)
        tmp21 = tmp19 < tmp20
        tmp22 = tl.load(in_ptr0 + (r1 + 32*x0), rmask & tmp21, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp23 = 0.0
        tmp24 = tl.where(tmp21, tmp22, tmp23)
        tmp26 = tmp24 + tmp25
        tmp28 = tmp26 + tmp27
        tmp30 = tmp28 + tmp29
        tmp31 = tmp30.to(tl.float32)
        tmp33 = tmp31 * tmp32
        tmp34 = -0.5
        tmp35 = tmp17 * tmp34
        tmp36 = tmp32 * tmp32
        tmp37 = tmp36 * tmp32
        tmp38 = tmp35 * tmp37
        tmp39 = 0.0026041666666666665
        tmp40 = tmp38 * tmp39
        tmp42 = tmp41.to(tl.float32)
        tmp43 = 2.0
        tmp44 = tmp42 * tmp43
        tmp45 = tmp40 * tmp44
        tmp46 = tmp33 + tmp45
        tmp47 = tmp46.to(tl.float32)
        tmp49 = tmp48 + tmp47
        tmp52 = tmp51.to(tl.float32)
        tmp53 = tmp49 * tmp52
        tl.store(in_out_ptr0 + (r1 + 384*x0), tmp47, rmask)
        tl.store(out_ptr1 + (r1 + 384*x0), tmp53, rmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/2n/c2n46zm2gvz3alwk7lpspbngtu2lywxqebqnlkox4l7crue3yziv.py
# Topologically Sorted Source Nodes: [loss, x_1, mul, mul_1, x_2, rms_norm_1], Original ATen: [aten.nll_loss_forward, aten._to_copy, aten.mul, aten.add, aten.embedding_dense_backward, aten.sum, aten.div, aten.pow]
# Source node to ATen node mapping:
#   loss => full_default_1
#   mul => mul_1
#   mul_1 => mul_2
#   rms_norm_1 => convert_element_type_2
#   x_1 => convert_element_type, convert_element_type_1, mul
#   x_2 => add_1
# Graph fragment:
#   %full_default_1 : [num_users=5] = call_function[target=torch.ops.aten.full.default](args = ([], 0.0), kwargs = {dtype: torch.float32, layout: torch.strided, device: cuda:0, pin_memory: False})
#   %convert_element_type : [num_users=3] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%embedding, torch.float32), kwargs = {})
#   %mul : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type, %rsqrt), kwargs = {})
#   %convert_element_type_1 : [num_users=8] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul, torch.bfloat16), kwargs = {})
#   %add_153 : [num_users=4] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_140, %convert_element_type_424), kwargs = {})
#   %convert_element_type_425 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%view_213, torch.float32), kwargs = {})
#   %where_11 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%unsqueeze_17, %full_default_1, %convert_element_type_425), kwargs = {})
#   %mul_305 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_153, %select_3), kwargs = {})
#   %mul_306 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_153, %convert_element_type_1), kwargs = {})
#   %sum_37 : [num_users=1] = call_function[target=torch.ops.aten.sum.default](args = (%mul_306,), kwargs = {dtype: torch.float32})
#   %add_154 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_136, %mul_305), kwargs = {})
#   %mul_308 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_153, %add_11), kwargs = {})
#   %sum_38 : [num_users=1] = call_function[target=torch.ops.aten.sum.default](args = (%mul_308,), kwargs = {dtype: torch.float32})
#   %add_167 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%view_234, %view_237), kwargs = {})
#   %add_168 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_167, %view_240), kwargs = {})
#   %convert_element_type_465 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_168, torch.float32), kwargs = {})
#   %mul_1 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%select, %convert_element_type_1), kwargs = {})
#   %mul_2 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%select_1, %convert_element_type_1), kwargs = {})
#   %add_1 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_1, %mul_2), kwargs = {})
#   %convert_element_type_2 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_1, torch.float32), kwargs = {})
#   %mul_337 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_465, %convert_element_type_2), kwargs = {})
#   %mul_338 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_465, %rsqrt_1), kwargs = {})
#   %sum_42 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mul_337, [2], True), kwargs = {dtype: torch.float32})
#   %div_28 : [num_users=1] = call_function[target=torch.ops.aten.div.Scalar](args = (%expand_36, 384), kwargs = {})
#   %pow_88 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_2, 1.0), kwargs = {})
#   %mul_341 : [num_users=1] = call_function[target=torch.ops.aten.mul.Scalar](args = (%pow_88, 2.0), kwargs = {})
#   %mul_342 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%div_28, %mul_341), kwargs = {})
#   %add_169 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_338, %mul_342), kwargs = {})
#   %convert_element_type_466 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_169, torch.bfloat16), kwargs = {})
#   %add_170 : [num_users=3] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_158, %convert_element_type_466), kwargs = {})
#   %mul_343 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_170, %select_1), kwargs = {})
#   %mul_344 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_170, %convert_element_type_1), kwargs = {})
#   %sum_43 : [num_users=1] = call_function[target=torch.ops.aten.sum.default](args = (%mul_344,), kwargs = {dtype: torch.float32})
#   %add_171 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_154, %mul_343), kwargs = {})
#   %mul_345 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_170, %select), kwargs = {})
#   %add_173 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_171, %mul_345), kwargs = {})
#   %convert_element_type_467 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_173, torch.float32), kwargs = {})
#   %mul_347 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_467, %convert_element_type), kwargs = {})
#   %mul_348 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_467, %rsqrt), kwargs = {})
#   %sum_45 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mul_347, [2], True), kwargs = {dtype: torch.float32})
#   %div_29 : [num_users=1] = call_function[target=torch.ops.aten.div.Scalar](args = (%expand_37, 384), kwargs = {})
#   %pow_90 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type, 1.0), kwargs = {})
#   %mul_351 : [num_users=1] = call_function[target=torch.ops.aten.mul.Scalar](args = (%pow_90, 2.0), kwargs = {})
#   %mul_352 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%div_29, %mul_351), kwargs = {})
#   %add_175 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_348, %mul_352), kwargs = {})
#   %where_13 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%unsqueeze_17, %full_default_1, %add_175), kwargs = {})
triton_per_fused__to_copy_add_div_embedding_dense_backward_mul_nll_loss_forward_pow_sum_24 = async_compile.triton('triton_per_fused__to_copy_add_div_embedding_dense_backward_mul_nll_loss_forward_pow_sum_24', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 32768, 'r': 512},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*fp32', 'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'in_ptr3': '*fp32', 'in_ptr4': '*bf16', 'in_ptr5': '*bf16', 'in_ptr6': '*bf16', 'in_ptr7': '*bf16', 'in_ptr8': '*fp32', 'in_ptr9': '*fp32', 'in_ptr10': '*fp32', 'in_ptr11': '*bf16', 'in_ptr12': '*bf16', 'in_ptr13': '*i64', 'in_ptr14': '*bf16', 'in_ptr15': '*bf16', 'out_ptr0': '*fp32', 'out_ptr1': '*fp32', 'out_ptr4': '*fp32', 'out_ptr6': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_div_embedding_dense_backward_mul_nll_loss_forward_pow_sum_24', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': True, 'num_load': 17, 'num_reduction': 5, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_div_embedding_dense_backward_mul_nll_loss_forward_pow_sum_24(in_out_ptr0, in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, in_ptr5, in_ptr6, in_ptr7, in_ptr8, in_ptr9, in_ptr10, in_ptr11, in_ptr12, in_ptr13, in_ptr14, in_ptr15, out_ptr0, out_ptr1, out_ptr4, out_ptr6, xnumel, rnumel):
    xnumel = 32768
    XBLOCK: tl.constexpr = 1
    rnumel = 384
    RBLOCK: tl.constexpr = 512
    xoffset = tl.program_id(0) * XBLOCK
    xindex = tl.full([1], xoffset, tl.int32)
    xmask = tl.full([RBLOCK], True, tl.int1)
    rindex = tl.arange(0, RBLOCK)[:]
    roffset = 0
    rmask = rindex < rnumel
    r1 = rindex
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp1 = tl.load(in_ptr1 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp3 = tl.load(in_ptr2 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp5 = tl.load(in_ptr3 + (x0), None, eviction_policy='evict_last')
    tmp14 = tl.load(in_ptr4 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp21 = tl.load(in_ptr5 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp22 = tl.load(in_ptr6 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp24 = tl.load(in_ptr7 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp27 = tl.load(in_ptr8 + (0))
    tmp28 = tl.broadcast_to(tmp27, [RBLOCK])
    tmp31 = tl.load(in_ptr9 + (0))
    tmp32 = tl.broadcast_to(tmp31, [RBLOCK])
    tmp42 = tl.load(in_ptr10 + (x0), None, eviction_policy='evict_last')
    tmp55 = tl.load(in_ptr11 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp56 = tl.load(in_ptr9 + (1))
    tmp57 = tl.broadcast_to(tmp56, [RBLOCK])
    tmp61 = tl.load(in_ptr12 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp80 = tl.load(in_ptr13 + (x0), None, eviction_policy='evict_last')
    tmp83 = tl.load(in_ptr14 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp84 = tl.load(in_ptr15 + (3*x0 + (r1 // 128)), rmask, eviction_policy='evict_last', other=0.0).to(tl.float32)
    tmp2 = tmp0 + tmp1
    tmp4 = tmp3.to(tl.float32)
    tmp6 = tmp4 * tmp5
    tmp7 = tmp6.to(tl.float32)
    tmp8 = tmp2 * tmp7
    tmp9 = tmp8.to(tl.float32)
    tmp10 = tl.broadcast_to(tmp9, [RBLOCK])
    tmp12 = tl.where(rmask, tmp10, 0)
    tmp13 = triton_helpers.promote_to_tensor(tl.sum(tmp12, 0))
    tmp15 = tmp2 * tmp14
    tmp16 = tmp15.to(tl.float32)
    tmp17 = tl.broadcast_to(tmp16, [RBLOCK])
    tmp19 = tl.where(rmask, tmp17, 0)
    tmp20 = triton_helpers.promote_to_tensor(tl.sum(tmp19, 0))
    tmp23 = tmp21 + tmp22
    tmp25 = tmp23 + tmp24
    tmp26 = tmp25.to(tl.float32)
    tmp29 = tmp28.to(tl.float32)
    tmp30 = tmp29 * tmp7
    tmp33 = tmp32.to(tl.float32)
    tmp34 = tmp33 * tmp7
    tmp35 = tmp30 + tmp34
    tmp36 = tmp35.to(tl.float32)
    tmp37 = tmp26 * tmp36
    tmp38 = tl.broadcast_to(tmp37, [RBLOCK])
    tmp40 = tl.where(rmask, tmp38, 0)
    tmp41 = triton_helpers.promote_to_tensor(tl.sum(tmp40, 0))
    tmp43 = tmp26 * tmp42
    tmp44 = -0.5
    tmp45 = tmp41 * tmp44
    tmp46 = tmp42 * tmp42
    tmp47 = tmp46 * tmp42
    tmp48 = tmp45 * tmp47
    tmp49 = 0.0026041666666666665
    tmp50 = tmp48 * tmp49
    tmp51 = 2.0
    tmp52 = tmp36 * tmp51
    tmp53 = tmp50 * tmp52
    tmp54 = tmp43 + tmp53
    tmp58 = tmp57.to(tl.float32)
    tmp59 = tmp2 * tmp58
    tmp60 = tmp55 + tmp59
    tmp62 = tmp54.to(tl.float32)
    tmp63 = tmp61 + tmp62
    tmp64 = tmp63 * tmp33
    tmp65 = tmp60 + tmp64
    tmp66 = tmp63 * tmp29
    tmp67 = tmp65 + tmp66
    tmp68 = tmp67.to(tl.float32)
    tmp69 = tmp63 * tmp7
    tmp70 = tmp69.to(tl.float32)
    tmp71 = tl.broadcast_to(tmp70, [RBLOCK])
    tmp73 = tl.where(rmask, tmp71, 0)
    tmp74 = triton_helpers.promote_to_tensor(tl.sum(tmp73, 0))
    tmp75 = tmp68 * tmp4
    tmp76 = tl.broadcast_to(tmp75, [RBLOCK])
    tmp78 = tl.where(rmask, tmp76, 0)
    tmp79 = triton_helpers.promote_to_tensor(tl.sum(tmp78, 0))
    tmp81 = tl.full([1], -1, tl.int64)
    tmp82 = tmp80 == tmp81
    tmp85 = tl.sigmoid(tmp84)
    tmp86 = tmp85 * tmp51
    tmp87 = tmp83 * tmp86
    tmp88 = tmp87.to(tl.float32)
    tmp89 = 0.0
    tmp90 = tl.where(tmp82, tmp89, tmp88)
    tmp91 = tmp68 * tmp5
    tmp92 = tmp79 * tmp44
    tmp93 = tmp5 * tmp5
    tmp94 = tmp93 * tmp5
    tmp95 = tmp92 * tmp94
    tmp96 = tmp95 * tmp49
    tmp97 = tmp4 * tmp51
    tmp98 = tmp96 * tmp97
    tmp99 = tmp91 + tmp98
    tmp100 = tl.where(tmp82, tmp89, tmp99)
    tl.store(out_ptr6 + (r1 + 384*x0), tmp90, rmask)
    tl.store(in_out_ptr0 + (r1 + 384*x0), tmp100, rmask)
    tl.store(out_ptr0 + (x0), tmp13, None)
    tl.store(out_ptr1 + (x0), tmp20, None)
    tl.store(out_ptr4 + (x0), tmp74, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/wc/cwcwoig7rmtzjgd7273lm2yye5ikvavupdriwe3moyhcmpupa5np.py
# Topologically Sorted Source Nodes: [], Original ATen: [aten.select_backward, aten.add]
# Source node to ATen node mapping:
# Graph fragment:
#   %full_default_13 : [num_users=11] = call_function[target=torch.ops.aten.full.default](args = ([6], 0), kwargs = {dtype: torch.float32, layout: torch.strided, device: cuda:0, pin_memory: False})
#   %select_scatter_default : [num_users=1] = call_function[target=torch.ops.aten.select_scatter.default](args = (%full_default_13, %sum_11, 0, 5), kwargs = {})
#   %select_scatter_default_2 : [num_users=1] = call_function[target=torch.ops.aten.select_scatter.default](args = (%full_default_13, %sum_17, 0, 4), kwargs = {})
#   %add_102 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%select_scatter_default, %select_scatter_default_2), kwargs = {})
#   %select_scatter_default_4 : [num_users=1] = call_function[target=torch.ops.aten.select_scatter.default](args = (%full_default_13, %sum_24, 0, 3), kwargs = {})
#   %add_120 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_102, %select_scatter_default_4), kwargs = {})
#   %select_scatter_default_6 : [num_users=1] = call_function[target=torch.ops.aten.select_scatter.default](args = (%full_default_13, %sum_30, 0, 2), kwargs = {})
#   %add_137 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_120, %select_scatter_default_6), kwargs = {})
#   %select_scatter_default_8 : [num_users=1] = call_function[target=torch.ops.aten.select_scatter.default](args = (%full_default_13, %sum_37, 0, 1), kwargs = {})
#   %add_155 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_137, %select_scatter_default_8), kwargs = {})
#   %select_scatter_default_10 : [num_users=2] = call_function[target=torch.ops.aten.select_scatter.default](args = (%full_default_13, %sum_43, 0, 0), kwargs = {})
#   %add_172 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_155, %select_scatter_default_10), kwargs = {})
triton_poi_fused_add_select_backward_25 = async_compile.triton('triton_poi_fused_add_select_backward_25', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.pointwise(
    size_hints={'x': 8}, 
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*fp32', 'in_ptr1': '*fp32', 'in_ptr2': '*fp32', 'in_ptr3': '*fp32', 'in_ptr4': '*fp32', 'in_ptr5': '*fp32', 'out_ptr0': '*fp32', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_add_select_backward_25', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 6, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_add_select_backward_25(in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, in_ptr5, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 6
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = xindex < xnumel
    x0 = xindex
    tmp3 = tl.load(in_ptr0 + (0))
    tmp4 = tl.broadcast_to(tmp3, [XBLOCK])
    tmp9 = tl.load(in_ptr1 + (0))
    tmp10 = tl.broadcast_to(tmp9, [XBLOCK])
    tmp15 = tl.load(in_ptr2 + (0))
    tmp16 = tl.broadcast_to(tmp15, [XBLOCK])
    tmp21 = tl.load(in_ptr3 + (0))
    tmp22 = tl.broadcast_to(tmp21, [XBLOCK])
    tmp27 = tl.load(in_ptr4 + (0))
    tmp28 = tl.broadcast_to(tmp27, [XBLOCK])
    tmp33 = tl.load(in_ptr5 + (0))
    tmp34 = tl.broadcast_to(tmp33, [XBLOCK])
    tmp0 = x0
    tmp1 = tl.full([1], 5, tl.int32)
    tmp2 = tmp0 == tmp1
    tmp5 = 0.0
    tmp6 = tl.where(tmp2, tmp4, tmp5)
    tmp7 = tl.full([1], 4, tl.int32)
    tmp8 = tmp0 == tmp7
    tmp11 = tl.where(tmp8, tmp10, tmp5)
    tmp12 = tmp6 + tmp11
    tmp13 = tl.full([1], 3, tl.int32)
    tmp14 = tmp0 == tmp13
    tmp17 = tl.where(tmp14, tmp16, tmp5)
    tmp18 = tmp12 + tmp17
    tmp19 = tl.full([1], 2, tl.int32)
    tmp20 = tmp0 == tmp19
    tmp23 = tl.where(tmp20, tmp22, tmp5)
    tmp24 = tmp18 + tmp23
    tmp25 = tl.full([1], 1, tl.int32)
    tmp26 = tmp0 == tmp25
    tmp29 = tl.where(tmp26, tmp28, tmp5)
    tmp30 = tmp24 + tmp29
    tmp31 = tl.full([1], 0, tl.int32)
    tmp32 = tmp0 == tmp31
    tmp35 = tl.where(tmp32, tmp34, tmp5)
    tmp36 = tmp30 + tmp35
    tl.store(out_ptr0 + (x0), tmp36, xmask)
''', device_str='cuda')


async_compile.wait(globals())
del async_compile

def call(args):
    primals_1, primals_5, primals_6, primals_50, slice_2, slice_4, embedding, rsqrt, rsqrt_1, view, cat, cat_1, rsqrt_2, rsqrt_3, permute_3, permute_4, permute_5, getitem, getitem_1, getitem_6, getitem_7, add_9, rsqrt_4, view_14, mm_4, view_16, add_11, add_12, embedding_1, rsqrt_5, view_18, view_28, mm_9, cat_2, cat_3, rsqrt_6, rsqrt_7, permute_14, permute_15, permute_16, getitem_9, getitem_10, getitem_15, getitem_16, add_21, rsqrt_8, view_35, mm_11, view_37, add_23, add_24, rsqrt_9, view_39, cat_4, cat_5, rsqrt_10, rsqrt_11, permute_24, permute_25, permute_26, getitem_18, getitem_19, getitem_24, getitem_25, add_32, rsqrt_12, view_53, mm_17, view_55, add_34, add_35, embedding_2, rsqrt_13, view_57, view_67, mm_22, cat_6, cat_7, rsqrt_14, rsqrt_15, permute_35, permute_36, permute_37, getitem_27, getitem_28, getitem_33, getitem_34, add_44, rsqrt_16, view_74, mm_24, view_76, add_46, add_47, rsqrt_17, view_78, cat_8, cat_9, rsqrt_18, rsqrt_19, permute_45, permute_46, permute_47, getitem_36, getitem_37, getitem_42, getitem_43, add_55, rsqrt_20, view_92, mm_30, view_94, add_57, add_58, embedding_3, rsqrt_21, view_96, view_106, mm_35, cat_10, cat_11, rsqrt_22, rsqrt_23, permute_56, permute_57, permute_58, getitem_45, getitem_46, getitem_51, getitem_52, add_67, rsqrt_24, view_113, mm_37, view_115, add_69, rsqrt_25, view_117, mm_39, amax, log, convert_element_type_185, permute_66, permute_70, permute_74, permute_78, permute_86, permute_90, permute_94, permute_98, permute_102, permute_106, permute_110, permute_118, permute_122, permute_126, permute_130, permute_134, permute_138, permute_146, permute_150, permute_154, permute_158, permute_162, permute_166, permute_170, permute_178, permute_182, permute_186, permute_190, permute_194, permute_198, permute_206, permute_210, permute_214, permute_218, permute_222, permute_226, permute_230, permute_238, permute_242, permute_246, tangents_1 = args
    args.clear()
    assert_size_stride(primals_1, (16, 2048), (2048, 1))
    assert_size_stride(primals_5, (6, ), (1, ))
    assert_size_stride(primals_6, (6, ), (1, ))
    assert_size_stride(primals_50, (16, 2048), (2048, 1))
    assert_size_stride(slice_2, (1, 2048, 1, 64), (1310720, 64, 64, 1))
    assert_size_stride(slice_4, (1, 2048, 1, 64), (1310720, 64, 64, 1))
    assert_size_stride(embedding, (16, 2048, 384), (786432, 384, 1))
    assert_size_stride(rsqrt, (16, 2048, 1), (2048, 1, 1))
    assert_size_stride(rsqrt_1, (16, 2048, 1), (2048, 1, 1))
    assert_size_stride(view, (32768, 384), (384, 1))
    assert_size_stride(cat, (16, 2048, 3, 128), (786432, 384, 128, 1))
    assert_size_stride(cat_1, (16, 2048, 3, 128), (786432, 384, 128, 1))
    assert_size_stride(rsqrt_2, (16, 2048, 3, 1), (6144, 3, 1, 1))
    assert_size_stride(rsqrt_3, (16, 2048, 3, 1), (6144, 3, 1, 1))
    assert_size_stride(permute_3, (16, 3, 2048, 128), (786432, 128, 384, 1))
    assert_size_stride(permute_4, (16, 3, 2048, 128), (786432, 128, 384, 1))
    assert_size_stride(permute_5, (16, 3, 2048, 128), (786432, 128, 384, 1))
    assert_size_stride(getitem, (16, 3, 2048, 128), (786432, 128, 384, 1))
    assert_size_stride(getitem_1, (16, 3, 2048), (6144, 2048, 1))
    assert_size_stride(getitem_6, (), ())
    assert_size_stride(getitem_7, (), ())
    assert_size_stride(add_9, (16, 2048, 384), (786432, 384, 1))
    assert_size_stride(rsqrt_4, (16, 2048, 1), (2048, 1, 1))
    assert_size_stride(view_14, (32768, 384), (384, 1))
    assert_size_stride(mm_4, (32768, 1536), (1536, 1))
    assert_size_stride(view_16, (32768, 1536), (1536, 1))
    assert_size_stride(add_11, (16, 2048, 384), (786432, 384, 1))
    assert_size_stride(add_12, (16, 2048, 384), (786432, 384, 1))
    assert_size_stride(embedding_1, (16, 2048, 384), (786432, 384, 1))
    assert_size_stride(rsqrt_5, (16, 2048, 1), (2048, 1, 1))
    assert_size_stride(view_18, (32768, 384), (384, 1))
    assert_size_stride(view_28, (32768, 32), (384, 1))
    assert_size_stride(mm_9, (32768, 3), (3, 1))
    assert_size_stride(cat_2, (16, 2048, 3, 128), (786432, 384, 128, 1))
    assert_size_stride(cat_3, (16, 2048, 3, 128), (786432, 384, 128, 1))
    assert_size_stride(rsqrt_6, (16, 2048, 3, 1), (6144, 3, 1, 1))
    assert_size_stride(rsqrt_7, (16, 2048, 3, 1), (6144, 3, 1, 1))
    assert_size_stride(permute_14, (16, 3, 2048, 128), (786432, 128, 384, 1))
    assert_size_stride(permute_15, (16, 3, 2048, 128), (786432, 128, 384, 1))
    assert_size_stride(permute_16, (16, 3, 2048, 128), (786432, 128, 384, 1))
    assert_size_stride(getitem_9, (16, 3, 2048, 128), (786432, 128, 384, 1))
    assert_size_stride(getitem_10, (16, 3, 2048), (6144, 2048, 1))
    assert_size_stride(getitem_15, (), ())
    assert_size_stride(getitem_16, (), ())
    assert_size_stride(add_21, (16, 2048, 384), (786432, 384, 1))
    assert_size_stride(rsqrt_8, (16, 2048, 1), (2048, 1, 1))
    assert_size_stride(view_35, (32768, 384), (384, 1))
    assert_size_stride(mm_11, (32768, 1536), (1536, 1))
    assert_size_stride(view_37, (32768, 1536), (1536, 1))
    assert_size_stride(add_23, (16, 2048, 384), (786432, 384, 1))
    assert_size_stride(add_24, (16, 2048, 384), (786432, 384, 1))
    assert_size_stride(rsqrt_9, (16, 2048, 1), (2048, 1, 1))
    assert_size_stride(view_39, (32768, 384), (384, 1))
    assert_size_stride(cat_4, (16, 2048, 3, 128), (786432, 384, 128, 1))
    assert_size_stride(cat_5, (16, 2048, 3, 128), (786432, 384, 128, 1))
    assert_size_stride(rsqrt_10, (16, 2048, 3, 1), (6144, 3, 1, 1))
    assert_size_stride(rsqrt_11, (16, 2048, 3, 1), (6144, 3, 1, 1))
    assert_size_stride(permute_24, (16, 3, 2048, 128), (786432, 128, 384, 1))
    assert_size_stride(permute_25, (16, 3, 2048, 128), (786432, 128, 384, 1))
    assert_size_stride(permute_26, (16, 3, 2048, 128), (786432, 128, 384, 1))
    assert_size_stride(getitem_18, (16, 3, 2048, 128), (786432, 128, 384, 1))
    assert_size_stride(getitem_19, (16, 3, 2048), (6144, 2048, 1))
    assert_size_stride(getitem_24, (), ())
    assert_size_stride(getitem_25, (), ())
    assert_size_stride(add_32, (16, 2048, 384), (786432, 384, 1))
    assert_size_stride(rsqrt_12, (16, 2048, 1), (2048, 1, 1))
    assert_size_stride(view_53, (32768, 384), (384, 1))
    assert_size_stride(mm_17, (32768, 1536), (1536, 1))
    assert_size_stride(view_55, (32768, 1536), (1536, 1))
    assert_size_stride(add_34, (16, 2048, 384), (786432, 384, 1))
    assert_size_stride(add_35, (16, 2048, 384), (786432, 384, 1))
    assert_size_stride(embedding_2, (16, 2048, 384), (786432, 384, 1))
    assert_size_stride(rsqrt_13, (16, 2048, 1), (2048, 1, 1))
    assert_size_stride(view_57, (32768, 384), (384, 1))
    assert_size_stride(view_67, (32768, 32), (384, 1))
    assert_size_stride(mm_22, (32768, 3), (3, 1))
    assert_size_stride(cat_6, (16, 2048, 3, 128), (786432, 384, 128, 1))
    assert_size_stride(cat_7, (16, 2048, 3, 128), (786432, 384, 128, 1))
    assert_size_stride(rsqrt_14, (16, 2048, 3, 1), (6144, 3, 1, 1))
    assert_size_stride(rsqrt_15, (16, 2048, 3, 1), (6144, 3, 1, 1))
    assert_size_stride(permute_35, (16, 3, 2048, 128), (786432, 128, 384, 1))
    assert_size_stride(permute_36, (16, 3, 2048, 128), (786432, 128, 384, 1))
    assert_size_stride(permute_37, (16, 3, 2048, 128), (786432, 128, 384, 1))
    assert_size_stride(getitem_27, (16, 3, 2048, 128), (786432, 128, 384, 1))
    assert_size_stride(getitem_28, (16, 3, 2048), (6144, 2048, 1))
    assert_size_stride(getitem_33, (), ())
    assert_size_stride(getitem_34, (), ())
    assert_size_stride(add_44, (16, 2048, 384), (786432, 384, 1))
    assert_size_stride(rsqrt_16, (16, 2048, 1), (2048, 1, 1))
    assert_size_stride(view_74, (32768, 384), (384, 1))
    assert_size_stride(mm_24, (32768, 1536), (1536, 1))
    assert_size_stride(view_76, (32768, 1536), (1536, 1))
    assert_size_stride(add_46, (16, 2048, 384), (786432, 384, 1))
    assert_size_stride(add_47, (16, 2048, 384), (786432, 384, 1))
    assert_size_stride(rsqrt_17, (16, 2048, 1), (2048, 1, 1))
    assert_size_stride(view_78, (32768, 384), (384, 1))
    assert_size_stride(cat_8, (16, 2048, 3, 128), (786432, 384, 128, 1))
    assert_size_stride(cat_9, (16, 2048, 3, 128), (786432, 384, 128, 1))
    assert_size_stride(rsqrt_18, (16, 2048, 3, 1), (6144, 3, 1, 1))
    assert_size_stride(rsqrt_19, (16, 2048, 3, 1), (6144, 3, 1, 1))
    assert_size_stride(permute_45, (16, 3, 2048, 128), (786432, 128, 384, 1))
    assert_size_stride(permute_46, (16, 3, 2048, 128), (786432, 128, 384, 1))
    assert_size_stride(permute_47, (16, 3, 2048, 128), (786432, 128, 384, 1))
    assert_size_stride(getitem_36, (16, 3, 2048, 128), (786432, 128, 384, 1))
    assert_size_stride(getitem_37, (16, 3, 2048), (6144, 2048, 1))
    assert_size_stride(getitem_42, (), ())
    assert_size_stride(getitem_43, (), ())
    assert_size_stride(add_55, (16, 2048, 384), (786432, 384, 1))
    assert_size_stride(rsqrt_20, (16, 2048, 1), (2048, 1, 1))
    assert_size_stride(view_92, (32768, 384), (384, 1))
    assert_size_stride(mm_30, (32768, 1536), (1536, 1))
    assert_size_stride(view_94, (32768, 1536), (1536, 1))
    assert_size_stride(add_57, (16, 2048, 384), (786432, 384, 1))
    assert_size_stride(add_58, (16, 2048, 384), (786432, 384, 1))
    assert_size_stride(embedding_3, (16, 2048, 384), (786432, 384, 1))
    assert_size_stride(rsqrt_21, (16, 2048, 1), (2048, 1, 1))
    assert_size_stride(view_96, (32768, 384), (384, 1))
    assert_size_stride(view_106, (32768, 32), (384, 1))
    assert_size_stride(mm_35, (32768, 3), (3, 1))
    assert_size_stride(cat_10, (16, 2048, 3, 128), (786432, 384, 128, 1))
    assert_size_stride(cat_11, (16, 2048, 3, 128), (786432, 384, 128, 1))
    assert_size_stride(rsqrt_22, (16, 2048, 3, 1), (6144, 3, 1, 1))
    assert_size_stride(rsqrt_23, (16, 2048, 3, 1), (6144, 3, 1, 1))
    assert_size_stride(permute_56, (16, 3, 2048, 128), (786432, 128, 384, 1))
    assert_size_stride(permute_57, (16, 3, 2048, 128), (786432, 128, 384, 1))
    assert_size_stride(permute_58, (16, 3, 2048, 128), (786432, 128, 384, 1))
    assert_size_stride(getitem_45, (16, 3, 2048, 128), (786432, 128, 384, 1))
    assert_size_stride(getitem_46, (16, 3, 2048), (6144, 2048, 1))
    assert_size_stride(getitem_51, (), ())
    assert_size_stride(getitem_52, (), ())
    assert_size_stride(add_67, (16, 2048, 384), (786432, 384, 1))
    assert_size_stride(rsqrt_24, (16, 2048, 1), (2048, 1, 1))
    assert_size_stride(view_113, (32768, 384), (384, 1))
    assert_size_stride(mm_37, (32768, 1536), (1536, 1))
    assert_size_stride(view_115, (32768, 1536), (1536, 1))
    assert_size_stride(add_69, (16, 2048, 384), (786432, 384, 1))
    assert_size_stride(rsqrt_25, (16, 2048, 1), (2048, 1, 1))
    assert_size_stride(view_117, (32768, 384), (384, 1))
    assert_size_stride(mm_39, (32768, 8192), (8192, 1))
    assert_size_stride(amax, (32768, 1), (1, 1))
    assert_size_stride(log, (32768, 1), (1, 1))
    assert_size_stride(convert_element_type_185, (), ())
    assert_size_stride(permute_66, (8192, 384), (384, 1))
    assert_size_stride(permute_70, (384, 1536), (1536, 1))
    assert_size_stride(permute_74, (1536, 384), (384, 1))
    assert_size_stride(permute_78, (384, 384), (384, 1))
    assert_size_stride(permute_86, (3, 32), (32, 1))
    assert_size_stride(permute_90, (384, 384), (384, 1))
    assert_size_stride(permute_94, (384, 384), (384, 1))
    assert_size_stride(permute_98, (384, 384), (384, 1))
    assert_size_stride(permute_102, (384, 1536), (1536, 1))
    assert_size_stride(permute_106, (1536, 384), (384, 1))
    assert_size_stride(permute_110, (384, 384), (384, 1))
    assert_size_stride(permute_118, (384, 384), (384, 1))
    assert_size_stride(permute_122, (384, 384), (384, 1))
    assert_size_stride(permute_126, (384, 384), (384, 1))
    assert_size_stride(permute_130, (384, 1536), (1536, 1))
    assert_size_stride(permute_134, (1536, 384), (384, 1))
    assert_size_stride(permute_138, (384, 384), (384, 1))
    assert_size_stride(permute_146, (3, 32), (32, 1))
    assert_size_stride(permute_150, (384, 384), (384, 1))
    assert_size_stride(permute_154, (384, 384), (384, 1))
    assert_size_stride(permute_158, (384, 384), (384, 1))
    assert_size_stride(permute_162, (384, 1536), (1536, 1))
    assert_size_stride(permute_166, (1536, 384), (384, 1))
    assert_size_stride(permute_170, (384, 384), (384, 1))
    assert_size_stride(permute_178, (384, 384), (384, 1))
    assert_size_stride(permute_182, (384, 384), (384, 1))
    assert_size_stride(permute_186, (384, 384), (384, 1))
    assert_size_stride(permute_190, (384, 1536), (1536, 1))
    assert_size_stride(permute_194, (1536, 384), (384, 1))
    assert_size_stride(permute_198, (384, 384), (384, 1))
    assert_size_stride(permute_206, (3, 32), (32, 1))
    assert_size_stride(permute_210, (384, 384), (384, 1))
    assert_size_stride(permute_214, (384, 384), (384, 1))
    assert_size_stride(permute_218, (384, 384), (384, 1))
    assert_size_stride(permute_222, (384, 1536), (1536, 1))
    assert_size_stride(permute_226, (1536, 384), (384, 1))
    assert_size_stride(permute_230, (384, 384), (384, 1))
    assert_size_stride(permute_238, (384, 384), (384, 1))
    assert_size_stride(permute_242, (384, 384), (384, 1))
    assert_size_stride(permute_246, (384, 384), (384, 1))
    assert_size_stride(tangents_1, (), ())
    with torch.cuda._DeviceGuard(0):
        torch.cuda.set_device(0)
        buf2 = reinterpret_tensor(mm_39, (16, 2048, 8192), (16777216, 8192, 1), 0); del mm_39  # reuse
        # Topologically Sorted Source Nodes: [loss, logits_1, truediv, tanh], Original ATen: [aten.nll_loss_backward, aten.nll_loss_forward, aten._to_copy, aten.div, aten.tanh, aten._log_softmax, aten._log_softmax_backward_data, aten.mul, aten.tanh_backward]
        stream0 = get_raw_stream(0)
        triton_red_fused__log_softmax__log_softmax_backward_data__to_copy_div_mul_nll_loss_backward_nll_loss_forward_tanh_tanh_backward_0.run(buf2, primals_50, tangents_1, convert_element_type_185, amax, log, 32768, 8192, grid=grid(32768), stream=stream0)
        del amax
        del convert_element_type_185
        del log
        del primals_50
        del tangents_1
        buf3 = empty_strided_cuda((8192, 384), (384, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf2, (8192, 32768), (1, 8192), 0), view_117, out=buf3)
        del view_117
        buf4 = empty_strided_cuda((32768, 384), (384, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf2, (32768, 8192), (8192, 1), 0), permute_66, out=buf4)
        del buf2
        del permute_66
        buf5 = empty_strided_cuda((8192, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_1.run(buf3, buf5, 3145728, grid=grid(3145728), stream=stream0)
        buf7 = reinterpret_tensor(buf4, (16, 2048, 384), (786432, 384, 1), 0); del buf4  # reuse
        # Topologically Sorted Source Nodes: [x_38], Original ATen: [aten._to_copy, aten.mul, aten.sum, aten.div, aten.pow, aten.add]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_div_mul_pow_sum_2.run(buf7, add_69, rsqrt_25, 32768, 384, grid=grid(32768), stream=stream0)
        del add_69
        del rsqrt_25
        buf8 = empty_strided_cuda((384, 1536), (1536, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf7, (384, 32768), (1, 384), 0), view_115, out=buf8)
        del view_115
        buf9 = empty_strided_cuda((32768, 1536), (1536, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf7, (32768, 384), (384, 1), 0), permute_70, out=buf9)
        del permute_70
        buf10 = empty_strided_cuda((384, 1536), (1536, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_3.run(buf8, buf10, 589824, grid=grid(589824), stream=stream0)
        buf11 = reinterpret_tensor(mm_37, (16, 2048, 1536), (3145728, 1536, 1), 0); del mm_37  # reuse
        # Topologically Sorted Source Nodes: [relu_5, x_35], Original ATen: [aten._to_copy, aten.relu, aten.pow, aten.mul, aten.threshold_backward]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_mul_pow_relu_threshold_backward_4.run(buf11, buf9, 50331648, grid=grid(50331648), stream=stream0)
        del buf9
        buf12 = reinterpret_tensor(buf8, (1536, 384), (384, 1), 0); del buf8  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf11, (1536, 32768), (1, 1536), 0), view_113, out=buf12)
        del view_113
        buf13 = empty_strided_cuda((32768, 384), (384, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf11, (32768, 1536), (1536, 1), 0), permute_74, out=buf13)
        del permute_74
        buf14 = empty_strided_cuda((1536, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_3.run(buf12, buf14, 589824, grid=grid(589824), stream=stream0)
        buf16 = buf7; del buf7  # reuse
        # Topologically Sorted Source Nodes: [rms_norm_24], Original ATen: [aten._to_copy, aten.mul, aten.sum, aten.div, aten.pow, aten.add]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_div_mul_pow_sum_5.run(buf16, buf13, add_67, rsqrt_24, 32768, 384, grid=grid(32768), stream=stream0)
        del add_67
        del rsqrt_24
        buf17 = empty_strided_cuda((384, 384), (384, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf16, (384, 32768), (1, 384), 0), reinterpret_tensor(getitem_45, (32768, 384), (384, 1), 0), out=buf17)
        buf18 = buf13; del buf13  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf16, (32768, 384), (384, 1), 0), permute_78, out=buf18)
        del permute_78
        buf19 = empty_strided_cuda((384, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf17, buf19, 147456, grid=grid(147456), stream=stream0)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._scaled_dot_product_flash_attention_backward]
        buf20 = torch.ops.aten._scaled_dot_product_flash_attention_backward.default(reinterpret_tensor(buf18, (16, 3, 2048, 128), (786432, 128, 384, 1), 0), permute_56, permute_57, permute_58, getitem_45, getitem_46, None, None, 2048, 2048, 0.0, True, getitem_51, getitem_52, scale=0.08838834764831843)
        del getitem_45
        del getitem_46
        del getitem_51
        del getitem_52
        del permute_56
        del permute_57
        del permute_58
        buf21 = buf20[0]
        buf22 = buf20[1]
        buf23 = buf20[2]
        del buf20
        buf24 = empty_strided_cuda((16, 2048, 3, 1), (6144, 3, 1, 98304), torch.float32)
        # Topologically Sorted Source Nodes: [k_27], Original ATen: [aten._to_copy, aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_mul_sum_7.run(buf22, cat_11, buf24, 98304, 128, grid=grid(98304), stream=stream0)
        buf25 = empty_strided_cuda((16, 2048, 3, 1), (6144, 3, 1, 98304), torch.float32)
        # Topologically Sorted Source Nodes: [q_22], Original ATen: [aten._to_copy, aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_mul_sum_7.run(buf21, cat_10, buf25, 98304, 128, grid=grid(98304), stream=stream0)
        buf26 = empty_strided_cuda((16, 2048, 3, 64), (393216, 192, 64, 1), torch.bfloat16)
        buf27 = empty_strided_cuda((16, 2048, 3, 64), (393216, 192, 64, 1), torch.bfloat16)
        buf28 = empty_strided_cuda((16, 2048, 3, 64), (393216, 192, 64, 1), torch.bfloat16)
        buf29 = empty_strided_cuda((16, 2048, 3, 64), (393216, 192, 64, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [neg], Original ATen: [aten.mul, aten.neg, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_mul_neg_8.run(buf22, rsqrt_23, buf24, cat_11, slice_2, slice_4, buf21, rsqrt_22, buf25, cat_10, buf26, buf27, buf28, buf29, 6291456, grid=grid(6291456), stream=stream0)
        del cat_10
        del cat_11
        del rsqrt_22
        del rsqrt_23
        buf49 = empty_strided_cuda((16, 2048, 384), (786432, 384, 1), torch.float32)
        buf31 = empty_strided_cuda((16, 2048, 3), (6144, 3, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [loss, sigmoid_2], Original ATen: [aten.nll_loss_forward, aten.sigmoid, aten.mul, aten.sum, aten.sigmoid_backward, aten.embedding_dense_backward]
        stream0 = get_raw_stream(0)
        triton_per_fused_embedding_dense_backward_mul_nll_loss_forward_sigmoid_sigmoid_backward_sum_9.run(buf23, embedding_3, primals_1, mm_35, buf49, buf31, 98304, 128, grid=grid(98304), stream=stream0)
        del embedding_3
        del mm_35
        buf32 = empty_strided_cuda((3, 32), (32, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf31, (3, 32768), (1, 3), 0), view_106, out=buf32)
        del view_106
        buf33 = empty_strided_cuda((32768, 32), (32, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf31, (32768, 3), (3, 1), 0), permute_86, out=buf33)
        del permute_86
        buf34 = empty_strided_cuda((3, 32), (32, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_10.run(buf32, buf34, 96, grid=grid(96), stream=stream0)
        buf35 = buf17; del buf17  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf23, (384, 32768), (1, 384), 0), view_96, out=buf35)
        buf36 = reinterpret_tensor(buf22, (32768, 384), (384, 1), 0); del buf22  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf23, (32768, 384), (384, 1), 0), permute_90, out=buf36)
        del permute_90
        buf37 = empty_strided_cuda((384, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf35, buf37, 147456, grid=grid(147456), stream=stream0)
        buf38 = reinterpret_tensor(buf23, (16, 2048, 3, 128), (786432, 384, 128, 1), 0); del buf23  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.slice_backward, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_slice_backward_11.run(buf26, buf27, buf38, 12582912, grid=grid(12582912), stream=stream0)
        buf39 = buf35; del buf35  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf38, (384, 32768), (1, 384), 0), view_96, out=buf39)
        buf40 = reinterpret_tensor(buf21, (32768, 384), (384, 1), 0); del buf21  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf38, (32768, 384), (384, 1), 0), permute_94, out=buf40)
        del permute_94
        buf41 = empty_strided_cuda((384, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf39, buf41, 147456, grid=grid(147456), stream=stream0)
        buf42 = buf38; del buf38  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.slice_backward, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_slice_backward_11.run(buf28, buf29, buf42, 12582912, grid=grid(12582912), stream=stream0)
        buf43 = buf39; del buf39  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf42, (384, 32768), (1, 384), 0), view_96, out=buf43)
        del view_96
        buf44 = buf18; del buf18  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf42, (32768, 384), (384, 1), 0), permute_98, out=buf44)
        del permute_98
        buf45 = empty_strided_cuda((384, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf43, buf45, 147456, grid=grid(147456), stream=stream0)
        buf47 = reinterpret_tensor(buf36, (16, 2048, 384), (786432, 384, 1), 0); del buf36  # reuse
        buf56 = reinterpret_tensor(buf42, (16, 2048, 384), (786432, 384, 1), 0); del buf42  # reuse
        # Topologically Sorted Source Nodes: [rms_norm_21], Original ATen: [aten.slice_backward, aten.add, aten._to_copy, aten.mul, aten.sum, aten.div, aten.pow]
        stream0 = get_raw_stream(0)
        triton_red_fused__to_copy_add_div_mul_pow_slice_backward_sum_12.run(buf47, buf33, buf40, buf44, add_58, rsqrt_21, buf16, primals_5, buf56, 32768, 384, grid=grid(32768), stream=stream0)
        del add_58
        del rsqrt_21
        buf48 = empty_strided_cuda((8192, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [loss], Original ATen: [aten.nll_loss_forward, aten.embedding_dense_backward]
        stream0 = get_raw_stream(0)
        triton_poi_fused_embedding_dense_backward_nll_loss_forward_13.run(buf48, 3145728, grid=grid(3145728), stream=stream0)
        aten.index_put_(buf48, [primals_1], buf49, True)
        buf51 = buf3; del buf3  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.embedding_dense_backward]
        stream0 = get_raw_stream(0)
        triton_poi_fused_embedding_dense_backward_14.run(buf48, buf51, 3145728, grid=grid(3145728), stream=stream0)
        buf58 = reinterpret_tensor(buf11, (32768, 1536), (1536, 1), 0); del buf11  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf56, (32768, 384), (384, 1), 0), permute_102, out=buf58)
        del permute_102
        buf60 = reinterpret_tensor(mm_30, (16, 2048, 1536), (3145728, 1536, 1), 0); del mm_30  # reuse
        # Topologically Sorted Source Nodes: [relu_4, x_29], Original ATen: [aten.threshold_backward, aten._to_copy, aten.relu, aten.pow, aten.mul]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_mul_pow_relu_threshold_backward_4.run(buf60, buf58, 50331648, grid=grid(50331648), stream=stream0)
        del buf58
        buf62 = buf44; del buf44  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf60, (32768, 1536), (1536, 1), 0), permute_106, out=buf62)
        del permute_106
        buf65 = reinterpret_tensor(buf62, (16, 2048, 384), (786432, 384, 1), 0); del buf62  # reuse
        # Topologically Sorted Source Nodes: [rms_norm_20], Original ATen: [aten._to_copy, aten.mul, aten.sum, aten.div, aten.pow, aten.add]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_div_mul_pow_sum_15.run(buf65, add_55, buf56, rsqrt_20, 32768, 384, grid=grid(32768), stream=stream0)
        del add_55
        del rsqrt_20
        buf67 = buf40; del buf40  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf65, (32768, 384), (384, 1), 0), permute_110, out=buf67)
        del permute_110
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._scaled_dot_product_flash_attention_backward]
        buf69 = torch.ops.aten._scaled_dot_product_flash_attention_backward.default(reinterpret_tensor(buf67, (16, 3, 2048, 128), (786432, 128, 384, 1), 0), permute_45, permute_46, permute_47, getitem_36, getitem_37, None, None, 2048, 2048, 0.0, True, getitem_42, getitem_43, scale=0.08838834764831843)
        del getitem_37
        del getitem_42
        del getitem_43
        del permute_45
        del permute_46
        del permute_47
        buf72 = buf69[2]
        buf80 = buf67; del buf67  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf72, (32768, 384), (384, 1), 0), permute_118, out=buf80)
        del permute_118
        buf70 = buf69[0]
        buf71 = buf69[1]
        del buf69
        buf73 = buf25; del buf25  # reuse
        # Topologically Sorted Source Nodes: [k_22], Original ATen: [aten._to_copy, aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_mul_sum_7.run(buf71, cat_9, buf73, 98304, 128, grid=grid(98304), stream=stream0)
        buf74 = buf24; del buf24  # reuse
        # Topologically Sorted Source Nodes: [q_18], Original ATen: [aten._to_copy, aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_mul_sum_7.run(buf70, cat_8, buf74, 98304, 128, grid=grid(98304), stream=stream0)
        buf75 = buf29; del buf29  # reuse
        buf76 = buf28; del buf28  # reuse
        buf77 = buf27; del buf27  # reuse
        buf78 = buf26; del buf26  # reuse
        # Topologically Sorted Source Nodes: [neg], Original ATen: [aten.neg, aten.mul, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_mul_neg_8.run(buf71, rsqrt_19, buf73, cat_9, slice_2, slice_4, buf70, rsqrt_18, buf74, cat_8, buf75, buf76, buf77, buf78, 6291456, grid=grid(6291456), stream=stream0)
        del cat_8
        del cat_9
        del rsqrt_18
        del rsqrt_19
        buf82 = reinterpret_tensor(buf71, (16, 2048, 3, 128), (786432, 384, 128, 1), 0); del buf71  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.slice_backward, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_slice_backward_11.run(buf75, buf76, buf82, 12582912, grid=grid(12582912), stream=stream0)
        buf84 = reinterpret_tensor(buf70, (32768, 384), (384, 1), 0); del buf70  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf82, (32768, 384), (384, 1), 0), permute_122, out=buf84)
        del permute_122
        buf86 = empty_strided_cuda((16, 2048, 3, 128), (786432, 384, 128, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.slice_backward, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_slice_backward_11.run(buf77, buf78, buf86, 12582912, grid=grid(12582912), stream=stream0)
        buf88 = empty_strided_cuda((32768, 384), (384, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf86, (32768, 384), (384, 1), 0), permute_126, out=buf88)
        del permute_126
        buf91 = reinterpret_tensor(buf80, (16, 2048, 384), (786432, 384, 1), 0); del buf80  # reuse
        buf96 = empty_strided_cuda((32768, 384), (384, 1), torch.bfloat16)
        buf52 = empty_strided_cuda((16, 2048, 1), (2048, 1, 32768), torch.float32)
        buf54 = empty_strided_cuda((16, 2048, 1), (2048, 1, 32768), torch.float32)
        buf92 = empty_strided_cuda((16, 2048, 1), (2048, 1, 32768), torch.float32)
        buf94 = empty_strided_cuda((16, 2048, 1), (2048, 1, 32768), torch.float32)
        # Topologically Sorted Source Nodes: [x_1, rms_norm_17], Original ATen: [aten.add, aten._to_copy, aten.mul, aten.sum, aten.div, aten.pow, aten.view]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_div_mul_pow_sum_view_16.run(buf91, buf84, buf88, add_47, buf65, rsqrt_17, primals_5, buf16, buf47, embedding, rsqrt, add_57, add_46, buf96, buf52, buf54, buf92, buf94, 32768, 384, grid=grid(32768), stream=stream0)
        del add_46
        del add_47
        del add_57
        del buf84
        del buf88
        del rsqrt_17
        buf53 = empty_strided_cuda((), (), torch.float32)
        # Topologically Sorted Source Nodes: [x_1], Original ATen: [aten.add, aten._to_copy, aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_red_fused__to_copy_add_mul_sum_17.run(buf52, buf53, 1, 32768, grid=grid(1), stream=stream0)
        buf55 = empty_strided_cuda((), (), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.add, aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_red_fused__to_copy_add_mul_sum_17.run(buf54, buf55, 1, 32768, grid=grid(1), stream=stream0)
        buf57 = reinterpret_tensor(buf12, (384, 1536), (1536, 1), 0); del buf12  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf56, (384, 32768), (1, 384), 0), view_94, out=buf57)
        del buf56
        del view_94
        buf59 = empty_strided_cuda((384, 1536), (1536, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_3.run(buf57, buf59, 589824, grid=grid(589824), stream=stream0)
        buf61 = reinterpret_tensor(buf57, (1536, 384), (384, 1), 0); del buf57  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf60, (1536, 32768), (1, 1536), 0), view_92, out=buf61)
        del view_92
        buf63 = empty_strided_cuda((1536, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_3.run(buf61, buf63, 589824, grid=grid(589824), stream=stream0)
        buf66 = buf43; del buf43  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf65, (384, 32768), (1, 384), 0), reinterpret_tensor(getitem_36, (32768, 384), (384, 1), 0), out=buf66)
        del getitem_36
        buf68 = empty_strided_cuda((384, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf66, buf68, 147456, grid=grid(147456), stream=stream0)
        buf79 = buf66; del buf66  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf72, (384, 32768), (1, 384), 0), view_78, out=buf79)
        buf81 = empty_strided_cuda((384, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf79, buf81, 147456, grid=grid(147456), stream=stream0)
        buf83 = buf79; del buf79  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf82, (384, 32768), (1, 384), 0), view_78, out=buf83)
        buf85 = empty_strided_cuda((384, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf83, buf85, 147456, grid=grid(147456), stream=stream0)
        buf87 = buf83; del buf83  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf86, (384, 32768), (1, 384), 0), view_78, out=buf87)
        del view_78
        buf89 = empty_strided_cuda((384, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf87, buf89, 147456, grid=grid(147456), stream=stream0)
        buf93 = empty_strided_cuda((), (), torch.float32)
        # Topologically Sorted Source Nodes: [x_1], Original ATen: [aten._to_copy, aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_red_fused__to_copy_add_mul_sum_17.run(buf92, buf93, 1, 32768, grid=grid(1), stream=stream0)
        buf95 = empty_strided_cuda((), (), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_red_fused__to_copy_add_mul_sum_17.run(buf94, buf95, 1, 32768, grid=grid(1), stream=stream0)
        buf97 = reinterpret_tensor(buf61, (384, 1536), (1536, 1), 0); del buf61  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf96, (384, 32768), (1, 384), 0), view_76, out=buf97)
        del view_76
        buf98 = reinterpret_tensor(buf60, (32768, 1536), (1536, 1), 0); del buf60  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(buf96, permute_130, out=buf98)
        del permute_130
        buf99 = empty_strided_cuda((384, 1536), (1536, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_3.run(buf97, buf99, 589824, grid=grid(589824), stream=stream0)
        buf100 = reinterpret_tensor(mm_24, (16, 2048, 1536), (3145728, 1536, 1), 0); del mm_24  # reuse
        # Topologically Sorted Source Nodes: [relu_3, x_23], Original ATen: [aten.threshold_backward, aten._to_copy, aten.relu, aten.pow, aten.mul]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_mul_pow_relu_threshold_backward_4.run(buf100, buf98, 50331648, grid=grid(50331648), stream=stream0)
        del buf98
        buf101 = reinterpret_tensor(buf97, (1536, 384), (384, 1), 0); del buf97  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf100, (1536, 32768), (1, 1536), 0), view_74, out=buf101)
        del view_74
        buf102 = buf96; del buf96  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf100, (32768, 1536), (1536, 1), 0), permute_134, out=buf102)
        del permute_134
        buf103 = empty_strided_cuda((1536, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_3.run(buf101, buf103, 589824, grid=grid(589824), stream=stream0)
        buf105 = reinterpret_tensor(buf102, (16, 2048, 384), (786432, 384, 1), 0); del buf102  # reuse
        # Topologically Sorted Source Nodes: [rms_norm_16], Original ATen: [aten.mul, aten._to_copy, aten.sum, aten.div, aten.pow, aten.add]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_div_mul_pow_sum_18.run(buf105, add_44, buf91, primals_5, rsqrt_16, 32768, 384, grid=grid(32768), stream=stream0)
        del add_44
        del rsqrt_16
        buf106 = buf87; del buf87  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf105, (384, 32768), (1, 384), 0), reinterpret_tensor(getitem_27, (32768, 384), (384, 1), 0), out=buf106)
        buf107 = reinterpret_tensor(buf86, (32768, 384), (384, 1), 0); del buf86  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf105, (32768, 384), (384, 1), 0), permute_138, out=buf107)
        del permute_138
        buf108 = empty_strided_cuda((384, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf106, buf108, 147456, grid=grid(147456), stream=stream0)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._scaled_dot_product_flash_attention_backward]
        buf109 = torch.ops.aten._scaled_dot_product_flash_attention_backward.default(reinterpret_tensor(buf107, (16, 3, 2048, 128), (786432, 128, 384, 1), 0), permute_35, permute_36, permute_37, getitem_27, getitem_28, None, None, 2048, 2048, 0.0, True, getitem_33, getitem_34, scale=0.08838834764831843)
        del getitem_27
        del getitem_28
        del getitem_33
        del getitem_34
        del permute_35
        del permute_36
        del permute_37
        buf110 = buf109[0]
        buf111 = buf109[1]
        buf112 = buf109[2]
        del buf109
        buf113 = buf74; del buf74  # reuse
        # Topologically Sorted Source Nodes: [k_17], Original ATen: [aten._to_copy, aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_mul_sum_7.run(buf111, cat_7, buf113, 98304, 128, grid=grid(98304), stream=stream0)
        buf114 = buf73; del buf73  # reuse
        # Topologically Sorted Source Nodes: [q_14], Original ATen: [aten._to_copy, aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_mul_sum_7.run(buf110, cat_6, buf114, 98304, 128, grid=grid(98304), stream=stream0)
        buf115 = buf78; del buf78  # reuse
        buf116 = buf77; del buf77  # reuse
        buf117 = buf76; del buf76  # reuse
        buf118 = buf75; del buf75  # reuse
        # Topologically Sorted Source Nodes: [neg], Original ATen: [aten.neg, aten.mul, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_mul_neg_8.run(buf111, rsqrt_15, buf113, cat_7, slice_2, slice_4, buf110, rsqrt_14, buf114, cat_6, buf115, buf116, buf117, buf118, 6291456, grid=grid(6291456), stream=stream0)
        del cat_6
        del cat_7
        del rsqrt_14
        del rsqrt_15
        buf138 = buf49; del buf49  # reuse
        buf120 = buf31; del buf31  # reuse
        # Topologically Sorted Source Nodes: [loss, sigmoid_1], Original ATen: [aten.nll_loss_forward, aten.sigmoid, aten.mul, aten.sum, aten.sigmoid_backward, aten.embedding_dense_backward]
        stream0 = get_raw_stream(0)
        triton_per_fused_embedding_dense_backward_mul_nll_loss_forward_sigmoid_sigmoid_backward_sum_9.run(buf112, embedding_2, primals_1, mm_22, buf138, buf120, 98304, 128, grid=grid(98304), stream=stream0)
        del embedding_2
        del mm_22
        buf121 = buf32; del buf32  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf120, (3, 32768), (1, 3), 0), view_67, out=buf121)
        del view_67
        buf122 = buf33; del buf33  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf120, (32768, 3), (3, 1), 0), permute_146, out=buf122)
        del permute_146
        buf123 = empty_strided_cuda((3, 32), (32, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_10.run(buf121, buf123, 96, grid=grid(96), stream=stream0)
        buf124 = buf106; del buf106  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf112, (384, 32768), (1, 384), 0), view_57, out=buf124)
        buf125 = reinterpret_tensor(buf111, (32768, 384), (384, 1), 0); del buf111  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf112, (32768, 384), (384, 1), 0), permute_150, out=buf125)
        del permute_150
        buf126 = empty_strided_cuda((384, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf124, buf126, 147456, grid=grid(147456), stream=stream0)
        buf127 = reinterpret_tensor(buf112, (16, 2048, 3, 128), (786432, 384, 128, 1), 0); del buf112  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.slice_backward, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_slice_backward_11.run(buf115, buf116, buf127, 12582912, grid=grid(12582912), stream=stream0)
        buf128 = buf124; del buf124  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf127, (384, 32768), (1, 384), 0), view_57, out=buf128)
        buf129 = reinterpret_tensor(buf110, (32768, 384), (384, 1), 0); del buf110  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf127, (32768, 384), (384, 1), 0), permute_154, out=buf129)
        del permute_154
        buf130 = empty_strided_cuda((384, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf128, buf130, 147456, grid=grid(147456), stream=stream0)
        buf131 = buf127; del buf127  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.slice_backward, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_slice_backward_11.run(buf117, buf118, buf131, 12582912, grid=grid(12582912), stream=stream0)
        buf132 = buf128; del buf128  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf131, (384, 32768), (1, 384), 0), view_57, out=buf132)
        del view_57
        buf133 = buf107; del buf107  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf131, (32768, 384), (384, 1), 0), permute_158, out=buf133)
        del permute_158
        buf134 = empty_strided_cuda((384, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf132, buf134, 147456, grid=grid(147456), stream=stream0)
        buf136 = reinterpret_tensor(buf125, (16, 2048, 384), (786432, 384, 1), 0); del buf125  # reuse
        buf145 = reinterpret_tensor(buf131, (16, 2048, 384), (786432, 384, 1), 0); del buf131  # reuse
        # Topologically Sorted Source Nodes: [rms_norm_13], Original ATen: [aten.slice_backward, aten.add, aten._to_copy, aten.mul, aten.sum, aten.div, aten.pow]
        stream0 = get_raw_stream(0)
        triton_red_fused__to_copy_add_div_mul_pow_slice_backward_sum_19.run(buf136, buf122, buf129, buf133, add_35, rsqrt_13, buf105, primals_5, buf145, 32768, 384, grid=grid(32768), stream=stream0)
        del add_35
        del rsqrt_13
        buf137 = buf48; del buf48  # reuse
        # Topologically Sorted Source Nodes: [loss], Original ATen: [aten.nll_loss_forward, aten.embedding_dense_backward]
        stream0 = get_raw_stream(0)
        triton_poi_fused_embedding_dense_backward_nll_loss_forward_13.run(buf137, 3145728, grid=grid(3145728), stream=stream0)
        aten.index_put_(buf137, [primals_1], buf138, True)
        buf140 = empty_strided_cuda((8192, 384), (384, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.embedding_dense_backward]
        stream0 = get_raw_stream(0)
        triton_poi_fused_embedding_dense_backward_14.run(buf137, buf140, 3145728, grid=grid(3145728), stream=stream0)
        buf147 = reinterpret_tensor(buf100, (32768, 1536), (1536, 1), 0); del buf100  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf145, (32768, 384), (384, 1), 0), permute_162, out=buf147)
        del permute_162
        buf149 = reinterpret_tensor(mm_17, (16, 2048, 1536), (3145728, 1536, 1), 0); del mm_17  # reuse
        # Topologically Sorted Source Nodes: [relu_2, x_17], Original ATen: [aten.threshold_backward, aten._to_copy, aten.relu, aten.pow, aten.mul]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_mul_pow_relu_threshold_backward_4.run(buf149, buf147, 50331648, grid=grid(50331648), stream=stream0)
        del buf147
        buf151 = buf133; del buf133  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf149, (32768, 1536), (1536, 1), 0), permute_166, out=buf151)
        del permute_166
        buf154 = reinterpret_tensor(buf151, (16, 2048, 384), (786432, 384, 1), 0); del buf151  # reuse
        # Topologically Sorted Source Nodes: [rms_norm_12], Original ATen: [aten._to_copy, aten.mul, aten.sum, aten.div, aten.pow, aten.add]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_div_mul_pow_sum_15.run(buf154, add_32, buf145, rsqrt_12, 32768, 384, grid=grid(32768), stream=stream0)
        del add_32
        del rsqrt_12
        buf156 = buf129; del buf129  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf154, (32768, 384), (384, 1), 0), permute_170, out=buf156)
        del permute_170
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._scaled_dot_product_flash_attention_backward]
        buf158 = torch.ops.aten._scaled_dot_product_flash_attention_backward.default(reinterpret_tensor(buf156, (16, 3, 2048, 128), (786432, 128, 384, 1), 0), permute_24, permute_25, permute_26, getitem_18, getitem_19, None, None, 2048, 2048, 0.0, True, getitem_24, getitem_25, scale=0.08838834764831843)
        del getitem_19
        del getitem_24
        del getitem_25
        del permute_24
        del permute_25
        del permute_26
        buf161 = buf158[2]
        buf169 = buf156; del buf156  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf161, (32768, 384), (384, 1), 0), permute_178, out=buf169)
        del permute_178
        buf159 = buf158[0]
        buf160 = buf158[1]
        del buf158
        buf162 = buf114; del buf114  # reuse
        # Topologically Sorted Source Nodes: [k_12], Original ATen: [aten._to_copy, aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_mul_sum_7.run(buf160, cat_5, buf162, 98304, 128, grid=grid(98304), stream=stream0)
        buf163 = buf113; del buf113  # reuse
        # Topologically Sorted Source Nodes: [q_10], Original ATen: [aten._to_copy, aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_mul_sum_7.run(buf159, cat_4, buf163, 98304, 128, grid=grid(98304), stream=stream0)
        buf164 = buf118; del buf118  # reuse
        buf165 = buf117; del buf117  # reuse
        buf166 = buf116; del buf116  # reuse
        buf167 = buf115; del buf115  # reuse
        # Topologically Sorted Source Nodes: [neg], Original ATen: [aten.neg, aten.mul, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_mul_neg_8.run(buf160, rsqrt_11, buf162, cat_5, slice_2, slice_4, buf159, rsqrt_10, buf163, cat_4, buf164, buf165, buf166, buf167, 6291456, grid=grid(6291456), stream=stream0)
        del cat_4
        del cat_5
        del rsqrt_10
        del rsqrt_11
        buf171 = reinterpret_tensor(buf160, (16, 2048, 3, 128), (786432, 384, 128, 1), 0); del buf160  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.slice_backward, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_slice_backward_11.run(buf164, buf165, buf171, 12582912, grid=grid(12582912), stream=stream0)
        buf173 = reinterpret_tensor(buf159, (32768, 384), (384, 1), 0); del buf159  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf171, (32768, 384), (384, 1), 0), permute_182, out=buf173)
        del permute_182
        buf175 = buf82; del buf82  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.slice_backward, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_slice_backward_11.run(buf166, buf167, buf175, 12582912, grid=grid(12582912), stream=stream0)
        buf177 = reinterpret_tensor(buf72, (32768, 384), (384, 1), 0); del buf72  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf175, (32768, 384), (384, 1), 0), permute_186, out=buf177)
        del permute_186
        buf180 = reinterpret_tensor(buf169, (16, 2048, 384), (786432, 384, 1), 0); del buf169  # reuse
        buf183 = buf16; del buf16  # reuse
        buf186 = reinterpret_tensor(buf65, (32768, 384), (384, 1), 0); del buf65  # reuse
        buf141 = buf94; del buf94  # reuse
        buf143 = buf92; del buf92  # reuse
        buf181 = buf54; del buf54  # reuse
        buf184 = buf52; del buf52  # reuse
        # Topologically Sorted Source Nodes: [x_1, rms_norm_9], Original ATen: [aten.add, aten.mul, aten._to_copy, aten.sum, aten.div, aten.pow, aten.view]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_div_mul_pow_sum_view_20.run(buf180, buf183, buf173, buf177, add_24, buf154, rsqrt_9, buf47, primals_6, buf91, buf105, buf136, primals_5, embedding, rsqrt, add_34, add_23, buf186, buf141, buf143, buf181, buf184, 32768, 384, grid=grid(32768), stream=stream0)
        del add_23
        del add_24
        del add_34
        del buf105
        del buf136
        del buf173
        del buf177
        del buf47
        del buf91
        del rsqrt_9
        buf142 = empty_strided_cuda((), (), torch.float32)
        # Topologically Sorted Source Nodes: [x_1], Original ATen: [aten._to_copy, aten.mul, aten.add, aten.sum]
        stream0 = get_raw_stream(0)
        triton_red_fused__to_copy_add_mul_sum_17.run(buf141, buf142, 1, 32768, grid=grid(1), stream=stream0)
        del buf141
        buf144 = empty_strided_cuda((), (), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.add, aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_red_fused__to_copy_add_mul_sum_17.run(buf143, buf144, 1, 32768, grid=grid(1), stream=stream0)
        buf146 = reinterpret_tensor(buf101, (384, 1536), (1536, 1), 0); del buf101  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf145, (384, 32768), (1, 384), 0), view_55, out=buf146)
        del buf145
        del view_55
        buf148 = empty_strided_cuda((384, 1536), (1536, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_3.run(buf146, buf148, 589824, grid=grid(589824), stream=stream0)
        buf150 = reinterpret_tensor(buf146, (1536, 384), (384, 1), 0); del buf146  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf149, (1536, 32768), (1, 1536), 0), view_53, out=buf150)
        del view_53
        buf152 = empty_strided_cuda((1536, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_3.run(buf150, buf152, 589824, grid=grid(589824), stream=stream0)
        buf155 = buf132; del buf132  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf154, (384, 32768), (1, 384), 0), reinterpret_tensor(getitem_18, (32768, 384), (384, 1), 0), out=buf155)
        del buf154
        del getitem_18
        buf157 = empty_strided_cuda((384, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf155, buf157, 147456, grid=grid(147456), stream=stream0)
        buf168 = buf155; del buf155  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf161, (384, 32768), (1, 384), 0), view_39, out=buf168)
        buf170 = empty_strided_cuda((384, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf168, buf170, 147456, grid=grid(147456), stream=stream0)
        buf172 = buf168; del buf168  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf171, (384, 32768), (1, 384), 0), view_39, out=buf172)
        buf174 = empty_strided_cuda((384, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf172, buf174, 147456, grid=grid(147456), stream=stream0)
        buf176 = buf172; del buf172  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf175, (384, 32768), (1, 384), 0), view_39, out=buf176)
        del view_39
        buf178 = empty_strided_cuda((384, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf176, buf178, 147456, grid=grid(147456), stream=stream0)
        buf182 = empty_strided_cuda((), (), torch.float32)
        # Topologically Sorted Source Nodes: [x_1], Original ATen: [aten._to_copy, aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_red_fused__to_copy_add_mul_sum_17.run(buf181, buf182, 1, 32768, grid=grid(1), stream=stream0)
        buf185 = empty_strided_cuda((), (), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_red_fused__to_copy_add_mul_sum_17.run(buf184, buf185, 1, 32768, grid=grid(1), stream=stream0)
        buf187 = reinterpret_tensor(buf150, (384, 1536), (1536, 1), 0); del buf150  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf186, (384, 32768), (1, 384), 0), view_37, out=buf187)
        del view_37
        buf188 = reinterpret_tensor(buf149, (32768, 1536), (1536, 1), 0); del buf149  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(buf186, permute_190, out=buf188)
        del permute_190
        buf189 = empty_strided_cuda((384, 1536), (1536, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_3.run(buf187, buf189, 589824, grid=grid(589824), stream=stream0)
        buf190 = reinterpret_tensor(mm_11, (16, 2048, 1536), (3145728, 1536, 1), 0); del mm_11  # reuse
        # Topologically Sorted Source Nodes: [relu_1, x_11], Original ATen: [aten.threshold_backward, aten._to_copy, aten.relu, aten.pow, aten.mul]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_mul_pow_relu_threshold_backward_4.run(buf190, buf188, 50331648, grid=grid(50331648), stream=stream0)
        del buf188
        buf191 = reinterpret_tensor(buf187, (1536, 384), (384, 1), 0); del buf187  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf190, (1536, 32768), (1, 1536), 0), view_35, out=buf191)
        del view_35
        buf192 = buf186; del buf186  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf190, (32768, 1536), (1536, 1), 0), permute_194, out=buf192)
        del permute_194
        buf193 = empty_strided_cuda((1536, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_3.run(buf191, buf193, 589824, grid=grid(589824), stream=stream0)
        buf195 = buf180; del buf180  # reuse
        # Topologically Sorted Source Nodes: [rms_norm_8], Original ATen: [aten.mul, aten._to_copy, aten.sum, aten.div, aten.pow, aten.add]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_div_mul_pow_sum_21.run(buf195, buf192, add_21, primals_5, rsqrt_8, 32768, 384, grid=grid(32768), stream=stream0)
        del add_21
        del rsqrt_8
        buf196 = buf176; del buf176  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf195, (384, 32768), (1, 384), 0), reinterpret_tensor(getitem_9, (32768, 384), (384, 1), 0), out=buf196)
        buf197 = buf192; del buf192  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf195, (32768, 384), (384, 1), 0), permute_198, out=buf197)
        del permute_198
        buf198 = empty_strided_cuda((384, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf196, buf198, 147456, grid=grid(147456), stream=stream0)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._scaled_dot_product_flash_attention_backward]
        buf199 = torch.ops.aten._scaled_dot_product_flash_attention_backward.default(reinterpret_tensor(buf197, (16, 3, 2048, 128), (786432, 128, 384, 1), 0), permute_14, permute_15, permute_16, getitem_9, getitem_10, None, None, 2048, 2048, 0.0, True, getitem_15, getitem_16, scale=0.08838834764831843)
        del getitem_10
        del getitem_15
        del getitem_16
        del getitem_9
        del permute_14
        del permute_15
        del permute_16
        buf200 = buf199[0]
        buf201 = buf199[1]
        buf202 = buf199[2]
        del buf199
        buf203 = buf163; del buf163  # reuse
        # Topologically Sorted Source Nodes: [k_7], Original ATen: [aten._to_copy, aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_mul_sum_7.run(buf201, cat_3, buf203, 98304, 128, grid=grid(98304), stream=stream0)
        buf204 = buf162; del buf162  # reuse
        # Topologically Sorted Source Nodes: [q_6], Original ATen: [aten._to_copy, aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_mul_sum_7.run(buf200, cat_2, buf204, 98304, 128, grid=grid(98304), stream=stream0)
        buf205 = buf167; del buf167  # reuse
        buf206 = buf166; del buf166  # reuse
        buf207 = buf165; del buf165  # reuse
        buf208 = buf164; del buf164  # reuse
        # Topologically Sorted Source Nodes: [neg], Original ATen: [aten.neg, aten.mul, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_mul_neg_8.run(buf201, rsqrt_7, buf203, cat_3, slice_2, slice_4, buf200, rsqrt_6, buf204, cat_2, buf205, buf206, buf207, buf208, 6291456, grid=grid(6291456), stream=stream0)
        del cat_2
        del cat_3
        del rsqrt_6
        del rsqrt_7
        buf210 = buf120; del buf120  # reuse
        # Topologically Sorted Source Nodes: [sigmoid], Original ATen: [aten.sigmoid, aten.mul, aten.sum, aten.sigmoid_backward]
        stream0 = get_raw_stream(0)
        triton_per_fused_mul_sigmoid_sigmoid_backward_sum_22.run(buf202, embedding_1, mm_9, buf210, 98304, 128, grid=grid(98304), stream=stream0)
        del embedding_1
        buf211 = buf121; del buf121  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf210, (3, 32768), (1, 3), 0), view_28, out=buf211)
        del view_28
        buf212 = buf122; del buf122  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf210, (32768, 3), (3, 1), 0), permute_206, out=buf212)
        del buf210
        del permute_206
        buf213 = empty_strided_cuda((3, 32), (32, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_10.run(buf211, buf213, 96, grid=grid(96), stream=stream0)
        del buf211
        buf214 = buf196; del buf196  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf202, (384, 32768), (1, 384), 0), view_18, out=buf214)
        buf215 = reinterpret_tensor(buf201, (32768, 384), (384, 1), 0); del buf201  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf202, (32768, 384), (384, 1), 0), permute_210, out=buf215)
        del permute_210
        buf216 = empty_strided_cuda((384, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf214, buf216, 147456, grid=grid(147456), stream=stream0)
        buf217 = reinterpret_tensor(buf200, (16, 2048, 3, 128), (786432, 384, 128, 1), 0); del buf200  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.slice_backward, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_slice_backward_11.run(buf205, buf206, buf217, 12582912, grid=grid(12582912), stream=stream0)
        buf218 = buf214; del buf214  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf217, (384, 32768), (1, 384), 0), view_18, out=buf218)
        buf219 = buf197; del buf197  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf217, (32768, 384), (384, 1), 0), permute_214, out=buf219)
        del permute_214
        buf220 = empty_strided_cuda((384, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf218, buf220, 147456, grid=grid(147456), stream=stream0)
        buf221 = buf217; del buf217  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.slice_backward, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_slice_backward_11.run(buf207, buf208, buf221, 12582912, grid=grid(12582912), stream=stream0)
        buf222 = buf218; del buf218  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf221, (384, 32768), (1, 384), 0), view_18, out=buf222)
        del view_18
        buf223 = reinterpret_tensor(buf175, (32768, 384), (384, 1), 0); del buf175  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf221, (32768, 384), (384, 1), 0), permute_218, out=buf223)
        del permute_218
        buf224 = empty_strided_cuda((384, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf222, buf224, 147456, grid=grid(147456), stream=stream0)
        buf226 = reinterpret_tensor(buf215, (16, 2048, 384), (786432, 384, 1), 0); del buf215  # reuse
        buf235 = reinterpret_tensor(buf221, (16, 2048, 384), (786432, 384, 1), 0); del buf221  # reuse
        # Topologically Sorted Source Nodes: [rms_norm_5], Original ATen: [aten.slice_backward, aten.add, aten._to_copy, aten.mul, aten.sum, aten.div, aten.pow]
        stream0 = get_raw_stream(0)
        triton_red_fused__to_copy_add_div_mul_pow_slice_backward_sum_23.run(buf226, buf212, buf219, buf223, add_12, rsqrt_5, buf195, primals_5, buf235, 32768, 384, grid=grid(32768), stream=stream0)
        del add_12
        del buf212
        del rsqrt_5
        buf227 = buf137; del buf137  # reuse
        # Topologically Sorted Source Nodes: [loss], Original ATen: [aten.nll_loss_forward, aten.embedding_dense_backward]
        stream0 = get_raw_stream(0)
        triton_poi_fused_embedding_dense_backward_nll_loss_forward_13.run(buf227, 3145728, grid=grid(3145728), stream=stream0)
        buf237 = reinterpret_tensor(buf190, (32768, 1536), (1536, 1), 0); del buf190  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf235, (32768, 384), (384, 1), 0), permute_222, out=buf237)
        del permute_222
        buf239 = reinterpret_tensor(mm_4, (16, 2048, 1536), (3145728, 1536, 1), 0); del mm_4  # reuse
        # Topologically Sorted Source Nodes: [relu, x_5], Original ATen: [aten.threshold_backward, aten._to_copy, aten.relu, aten.pow, aten.mul]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_mul_pow_relu_threshold_backward_4.run(buf239, buf237, 50331648, grid=grid(50331648), stream=stream0)
        del buf237
        buf241 = buf223; del buf223  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf239, (32768, 1536), (1536, 1), 0), permute_226, out=buf241)
        del permute_226
        buf244 = reinterpret_tensor(buf241, (16, 2048, 384), (786432, 384, 1), 0); del buf241  # reuse
        # Topologically Sorted Source Nodes: [rms_norm_4], Original ATen: [aten._to_copy, aten.mul, aten.sum, aten.div, aten.pow, aten.add]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_div_mul_pow_sum_15.run(buf244, add_9, buf235, rsqrt_4, 32768, 384, grid=grid(32768), stream=stream0)
        del add_9
        del rsqrt_4
        buf246 = buf219; del buf219  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf244, (32768, 384), (384, 1), 0), permute_230, out=buf246)
        del permute_230
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._scaled_dot_product_flash_attention_backward]
        buf248 = torch.ops.aten._scaled_dot_product_flash_attention_backward.default(reinterpret_tensor(buf246, (16, 3, 2048, 128), (786432, 128, 384, 1), 0), permute_3, permute_4, permute_5, getitem, getitem_1, None, None, 2048, 2048, 0.0, True, getitem_6, getitem_7, scale=0.08838834764831843)
        del getitem_1
        del getitem_6
        del getitem_7
        del permute_3
        del permute_4
        del permute_5
        buf251 = buf248[2]
        buf259 = buf246; del buf246  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf251, (32768, 384), (384, 1), 0), permute_238, out=buf259)
        del permute_238
        buf249 = buf248[0]
        buf250 = buf248[1]
        del buf248
        buf252 = buf204; del buf204  # reuse
        # Topologically Sorted Source Nodes: [k_2], Original ATen: [aten._to_copy, aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_mul_sum_7.run(buf250, cat_1, buf252, 98304, 128, grid=grid(98304), stream=stream0)
        buf253 = buf203; del buf203  # reuse
        # Topologically Sorted Source Nodes: [q_2], Original ATen: [aten._to_copy, aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_mul_sum_7.run(buf249, cat, buf253, 98304, 128, grid=grid(98304), stream=stream0)
        buf254 = buf208; del buf208  # reuse
        buf255 = buf207; del buf207  # reuse
        buf256 = buf206; del buf206  # reuse
        buf257 = buf205; del buf205  # reuse
        # Topologically Sorted Source Nodes: [neg], Original ATen: [aten.neg, aten.mul, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_mul_neg_8.run(buf250, rsqrt_3, buf252, cat_1, slice_2, slice_4, buf249, rsqrt_2, buf253, cat, buf254, buf255, buf256, buf257, 6291456, grid=grid(6291456), stream=stream0)
        del buf252
        del buf253
        del cat
        del cat_1
        del rsqrt_2
        del rsqrt_3
        del slice_2
        del slice_4
        buf261 = reinterpret_tensor(buf250, (16, 2048, 3, 128), (786432, 384, 128, 1), 0); del buf250  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.slice_backward, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_slice_backward_11.run(buf254, buf255, buf261, 12582912, grid=grid(12582912), stream=stream0)
        del buf254
        del buf255
        buf263 = reinterpret_tensor(buf249, (32768, 384), (384, 1), 0); del buf249  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf261, (32768, 384), (384, 1), 0), permute_242, out=buf263)
        del permute_242
        buf265 = buf171; del buf171  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.slice_backward, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_slice_backward_11.run(buf256, buf257, buf265, 12582912, grid=grid(12582912), stream=stream0)
        del buf256
        del buf257
        buf267 = reinterpret_tensor(buf161, (32768, 384), (384, 1), 0); del buf161  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf265, (32768, 384), (384, 1), 0), permute_246, out=buf267)
        del permute_246
        buf231 = buf184; del buf184  # reuse
        buf233 = buf181; del buf181  # reuse
        buf275 = buf138; del buf138  # reuse
        buf271 = buf143; del buf143  # reuse
        buf228 = empty_strided_cuda((16, 2048, 384), (786432, 384, 1), torch.float32)
        buf278 = buf275; del buf275  # reuse
        # Topologically Sorted Source Nodes: [loss, x_1, mul, mul_1, x_2, rms_norm_1], Original ATen: [aten.nll_loss_forward, aten._to_copy, aten.mul, aten.add, aten.embedding_dense_backward, aten.sum, aten.div, aten.pow]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_div_embedding_dense_backward_mul_nll_loss_forward_pow_sum_24.run(buf278, buf195, buf226, embedding, rsqrt, add_11, buf259, buf263, buf267, primals_5, primals_6, rsqrt_1, buf183, buf244, primals_1, buf202, mm_9, buf231, buf233, buf271, buf228, 32768, 384, grid=grid(32768), stream=stream0)
        del add_11
        del buf183
        del buf195
        del buf202
        del buf226
        del buf259
        del buf263
        del buf267
        del embedding
        del mm_9
        del primals_5
        del primals_6
        del rsqrt
        del rsqrt_1
        aten.index_put_(buf227, [primals_1], buf228, True)
        del buf228
        buf230 = empty_strided_cuda((8192, 384), (384, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.embedding_dense_backward]
        stream0 = get_raw_stream(0)
        triton_poi_fused_embedding_dense_backward_14.run(buf227, buf230, 3145728, grid=grid(3145728), stream=stream0)
        buf232 = empty_strided_cuda((), (), torch.float32)
        # Topologically Sorted Source Nodes: [x_1], Original ATen: [aten._to_copy, aten.mul, aten.add, aten.sum]
        stream0 = get_raw_stream(0)
        triton_red_fused__to_copy_add_mul_sum_17.run(buf231, buf232, 1, 32768, grid=grid(1), stream=stream0)
        del buf231
        buf234 = empty_strided_cuda((), (), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.add, aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_red_fused__to_copy_add_mul_sum_17.run(buf233, buf234, 1, 32768, grid=grid(1), stream=stream0)
        del buf233
        buf236 = reinterpret_tensor(buf191, (384, 1536), (1536, 1), 0); del buf191  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf235, (384, 32768), (1, 384), 0), view_16, out=buf236)
        del buf235
        del view_16
        buf238 = empty_strided_cuda((384, 1536), (1536, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_3.run(buf236, buf238, 589824, grid=grid(589824), stream=stream0)
        buf240 = reinterpret_tensor(buf236, (1536, 384), (384, 1), 0); del buf236  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf239, (1536, 32768), (1, 1536), 0), view_14, out=buf240)
        del buf239
        del view_14
        buf242 = empty_strided_cuda((1536, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_3.run(buf240, buf242, 589824, grid=grid(589824), stream=stream0)
        del buf240
        buf245 = buf222; del buf222  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf244, (384, 32768), (1, 384), 0), reinterpret_tensor(getitem, (32768, 384), (384, 1), 0), out=buf245)
        del buf244
        del getitem
        buf247 = empty_strided_cuda((384, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf245, buf247, 147456, grid=grid(147456), stream=stream0)
        buf258 = buf245; del buf245  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf251, (384, 32768), (1, 384), 0), view, out=buf258)
        del buf251
        buf260 = empty_strided_cuda((384, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf258, buf260, 147456, grid=grid(147456), stream=stream0)
        buf262 = buf258; del buf258  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf261, (384, 32768), (1, 384), 0), view, out=buf262)
        del buf261
        buf264 = empty_strided_cuda((384, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf262, buf264, 147456, grid=grid(147456), stream=stream0)
        buf266 = buf262; del buf262  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf265, (384, 32768), (1, 384), 0), view, out=buf266)
        del buf265
        del view
        buf268 = empty_strided_cuda((384, 384), (384, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf266, buf268, 147456, grid=grid(147456), stream=stream0)
        del buf266
        buf272 = empty_strided_cuda((), (), torch.float32)
        # Topologically Sorted Source Nodes: [x_1], Original ATen: [aten._to_copy, aten.mul, aten.add, aten.sum]
        stream0 = get_raw_stream(0)
        triton_red_fused__to_copy_add_mul_sum_17.run(buf271, buf272, 1, 32768, grid=grid(1), stream=stream0)
        del buf271
        buf273 = empty_strided_cuda((6, ), (1, ), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.select_backward, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_select_backward_25.run(buf53, buf93, buf142, buf182, buf232, buf272, buf273, 6, grid=grid(6), stream=stream0)
        del buf142
        del buf182
        del buf232
        del buf53
        del buf93
        buf274 = empty_strided_cuda((6, ), (1, ), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.select_backward, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_select_backward_25.run(buf55, buf95, buf144, buf185, buf234, buf272, buf274, 6, grid=grid(6), stream=stream0)
        del buf144
        del buf185
        del buf234
        del buf272
        del buf55
        del buf95
        buf277 = buf227; del buf227  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.embedding_dense_backward]
        stream0 = get_raw_stream(0)
        triton_poi_fused_embedding_dense_backward_nll_loss_forward_13.run(buf277, 3145728, grid=grid(3145728), stream=stream0)
        aten.index_put_(buf277, [primals_1], buf278, True)
        del buf278
        del primals_1
        buf280 = empty_strided_cuda((8192, 384), (384, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.embedding_dense_backward]
        stream0 = get_raw_stream(0)
        triton_poi_fused_embedding_dense_backward_14.run(buf277, buf280, 3145728, grid=grid(3145728), stream=stream0)
        del buf277
    return (None, None, None, buf280, buf274, buf273, buf268, buf264, buf260, buf247, buf242, buf238, buf230, buf224, buf220, buf216, buf213, buf198, buf193, buf189, buf178, buf174, buf170, buf157, buf152, buf148, buf140, buf134, buf130, buf126, buf123, buf108, buf103, buf99, buf89, buf85, buf81, buf68, buf63, buf59, buf51, buf45, buf41, buf37, buf34, buf19, buf14, buf10, buf5, None, )


def benchmark_compiled_module(times=10, repeat=10):
    from torch._dynamo.testing import rand_strided
    from torch._inductor.utils import print_performance
    primals_1 = rand_strided((16, 2048), (2048, 1), device='cuda:0', dtype=torch.int64)
    primals_5 = rand_strided((6, ), (1, ), device='cuda:0', dtype=torch.float32)
    primals_6 = rand_strided((6, ), (1, ), device='cuda:0', dtype=torch.float32)
    primals_50 = rand_strided((16, 2048), (2048, 1), device='cuda:0', dtype=torch.int64)
    slice_2 = rand_strided((1, 2048, 1, 64), (1310720, 64, 64, 1), device='cuda:0', dtype=torch.bfloat16)
    slice_4 = rand_strided((1, 2048, 1, 64), (1310720, 64, 64, 1), device='cuda:0', dtype=torch.bfloat16)
    embedding = rand_strided((16, 2048, 384), (786432, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt = rand_strided((16, 2048, 1), (2048, 1, 1), device='cuda:0', dtype=torch.float32)
    rsqrt_1 = rand_strided((16, 2048, 1), (2048, 1, 1), device='cuda:0', dtype=torch.float32)
    view = rand_strided((32768, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    cat = rand_strided((16, 2048, 3, 128), (786432, 384, 128, 1), device='cuda:0', dtype=torch.bfloat16)
    cat_1 = rand_strided((16, 2048, 3, 128), (786432, 384, 128, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt_2 = rand_strided((16, 2048, 3, 1), (6144, 3, 1, 1), device='cuda:0', dtype=torch.float32)
    rsqrt_3 = rand_strided((16, 2048, 3, 1), (6144, 3, 1, 1), device='cuda:0', dtype=torch.float32)
    permute_3 = rand_strided((16, 3, 2048, 128), (786432, 128, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_4 = rand_strided((16, 3, 2048, 128), (786432, 128, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_5 = rand_strided((16, 3, 2048, 128), (786432, 128, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    getitem = rand_strided((16, 3, 2048, 128), (786432, 128, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    getitem_1 = rand_strided((16, 3, 2048), (6144, 2048, 1), device='cuda:0', dtype=torch.float32)
    getitem_6 = rand_strided((), (), device='cuda:0', dtype=torch.int64)
    getitem_7 = rand_strided((), (), device='cuda:0', dtype=torch.int64)
    add_9 = rand_strided((16, 2048, 384), (786432, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt_4 = rand_strided((16, 2048, 1), (2048, 1, 1), device='cuda:0', dtype=torch.float32)
    view_14 = rand_strided((32768, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    mm_4 = rand_strided((32768, 1536), (1536, 1), device='cuda:0', dtype=torch.bfloat16)
    view_16 = rand_strided((32768, 1536), (1536, 1), device='cuda:0', dtype=torch.bfloat16)
    add_11 = rand_strided((16, 2048, 384), (786432, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    add_12 = rand_strided((16, 2048, 384), (786432, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    embedding_1 = rand_strided((16, 2048, 384), (786432, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt_5 = rand_strided((16, 2048, 1), (2048, 1, 1), device='cuda:0', dtype=torch.float32)
    view_18 = rand_strided((32768, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    view_28 = rand_strided((32768, 32), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    mm_9 = rand_strided((32768, 3), (3, 1), device='cuda:0', dtype=torch.bfloat16)
    cat_2 = rand_strided((16, 2048, 3, 128), (786432, 384, 128, 1), device='cuda:0', dtype=torch.bfloat16)
    cat_3 = rand_strided((16, 2048, 3, 128), (786432, 384, 128, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt_6 = rand_strided((16, 2048, 3, 1), (6144, 3, 1, 1), device='cuda:0', dtype=torch.float32)
    rsqrt_7 = rand_strided((16, 2048, 3, 1), (6144, 3, 1, 1), device='cuda:0', dtype=torch.float32)
    permute_14 = rand_strided((16, 3, 2048, 128), (786432, 128, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_15 = rand_strided((16, 3, 2048, 128), (786432, 128, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_16 = rand_strided((16, 3, 2048, 128), (786432, 128, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    getitem_9 = rand_strided((16, 3, 2048, 128), (786432, 128, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    getitem_10 = rand_strided((16, 3, 2048), (6144, 2048, 1), device='cuda:0', dtype=torch.float32)
    getitem_15 = rand_strided((), (), device='cuda:0', dtype=torch.int64)
    getitem_16 = rand_strided((), (), device='cuda:0', dtype=torch.int64)
    add_21 = rand_strided((16, 2048, 384), (786432, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt_8 = rand_strided((16, 2048, 1), (2048, 1, 1), device='cuda:0', dtype=torch.float32)
    view_35 = rand_strided((32768, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    mm_11 = rand_strided((32768, 1536), (1536, 1), device='cuda:0', dtype=torch.bfloat16)
    view_37 = rand_strided((32768, 1536), (1536, 1), device='cuda:0', dtype=torch.bfloat16)
    add_23 = rand_strided((16, 2048, 384), (786432, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    add_24 = rand_strided((16, 2048, 384), (786432, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt_9 = rand_strided((16, 2048, 1), (2048, 1, 1), device='cuda:0', dtype=torch.float32)
    view_39 = rand_strided((32768, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    cat_4 = rand_strided((16, 2048, 3, 128), (786432, 384, 128, 1), device='cuda:0', dtype=torch.bfloat16)
    cat_5 = rand_strided((16, 2048, 3, 128), (786432, 384, 128, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt_10 = rand_strided((16, 2048, 3, 1), (6144, 3, 1, 1), device='cuda:0', dtype=torch.float32)
    rsqrt_11 = rand_strided((16, 2048, 3, 1), (6144, 3, 1, 1), device='cuda:0', dtype=torch.float32)
    permute_24 = rand_strided((16, 3, 2048, 128), (786432, 128, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_25 = rand_strided((16, 3, 2048, 128), (786432, 128, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_26 = rand_strided((16, 3, 2048, 128), (786432, 128, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    getitem_18 = rand_strided((16, 3, 2048, 128), (786432, 128, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    getitem_19 = rand_strided((16, 3, 2048), (6144, 2048, 1), device='cuda:0', dtype=torch.float32)
    getitem_24 = rand_strided((), (), device='cuda:0', dtype=torch.int64)
    getitem_25 = rand_strided((), (), device='cuda:0', dtype=torch.int64)
    add_32 = rand_strided((16, 2048, 384), (786432, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt_12 = rand_strided((16, 2048, 1), (2048, 1, 1), device='cuda:0', dtype=torch.float32)
    view_53 = rand_strided((32768, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    mm_17 = rand_strided((32768, 1536), (1536, 1), device='cuda:0', dtype=torch.bfloat16)
    view_55 = rand_strided((32768, 1536), (1536, 1), device='cuda:0', dtype=torch.bfloat16)
    add_34 = rand_strided((16, 2048, 384), (786432, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    add_35 = rand_strided((16, 2048, 384), (786432, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    embedding_2 = rand_strided((16, 2048, 384), (786432, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt_13 = rand_strided((16, 2048, 1), (2048, 1, 1), device='cuda:0', dtype=torch.float32)
    view_57 = rand_strided((32768, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    view_67 = rand_strided((32768, 32), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    mm_22 = rand_strided((32768, 3), (3, 1), device='cuda:0', dtype=torch.bfloat16)
    cat_6 = rand_strided((16, 2048, 3, 128), (786432, 384, 128, 1), device='cuda:0', dtype=torch.bfloat16)
    cat_7 = rand_strided((16, 2048, 3, 128), (786432, 384, 128, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt_14 = rand_strided((16, 2048, 3, 1), (6144, 3, 1, 1), device='cuda:0', dtype=torch.float32)
    rsqrt_15 = rand_strided((16, 2048, 3, 1), (6144, 3, 1, 1), device='cuda:0', dtype=torch.float32)
    permute_35 = rand_strided((16, 3, 2048, 128), (786432, 128, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_36 = rand_strided((16, 3, 2048, 128), (786432, 128, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_37 = rand_strided((16, 3, 2048, 128), (786432, 128, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    getitem_27 = rand_strided((16, 3, 2048, 128), (786432, 128, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    getitem_28 = rand_strided((16, 3, 2048), (6144, 2048, 1), device='cuda:0', dtype=torch.float32)
    getitem_33 = rand_strided((), (), device='cuda:0', dtype=torch.int64)
    getitem_34 = rand_strided((), (), device='cuda:0', dtype=torch.int64)
    add_44 = rand_strided((16, 2048, 384), (786432, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt_16 = rand_strided((16, 2048, 1), (2048, 1, 1), device='cuda:0', dtype=torch.float32)
    view_74 = rand_strided((32768, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    mm_24 = rand_strided((32768, 1536), (1536, 1), device='cuda:0', dtype=torch.bfloat16)
    view_76 = rand_strided((32768, 1536), (1536, 1), device='cuda:0', dtype=torch.bfloat16)
    add_46 = rand_strided((16, 2048, 384), (786432, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    add_47 = rand_strided((16, 2048, 384), (786432, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt_17 = rand_strided((16, 2048, 1), (2048, 1, 1), device='cuda:0', dtype=torch.float32)
    view_78 = rand_strided((32768, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    cat_8 = rand_strided((16, 2048, 3, 128), (786432, 384, 128, 1), device='cuda:0', dtype=torch.bfloat16)
    cat_9 = rand_strided((16, 2048, 3, 128), (786432, 384, 128, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt_18 = rand_strided((16, 2048, 3, 1), (6144, 3, 1, 1), device='cuda:0', dtype=torch.float32)
    rsqrt_19 = rand_strided((16, 2048, 3, 1), (6144, 3, 1, 1), device='cuda:0', dtype=torch.float32)
    permute_45 = rand_strided((16, 3, 2048, 128), (786432, 128, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_46 = rand_strided((16, 3, 2048, 128), (786432, 128, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_47 = rand_strided((16, 3, 2048, 128), (786432, 128, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    getitem_36 = rand_strided((16, 3, 2048, 128), (786432, 128, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    getitem_37 = rand_strided((16, 3, 2048), (6144, 2048, 1), device='cuda:0', dtype=torch.float32)
    getitem_42 = rand_strided((), (), device='cuda:0', dtype=torch.int64)
    getitem_43 = rand_strided((), (), device='cuda:0', dtype=torch.int64)
    add_55 = rand_strided((16, 2048, 384), (786432, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt_20 = rand_strided((16, 2048, 1), (2048, 1, 1), device='cuda:0', dtype=torch.float32)
    view_92 = rand_strided((32768, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    mm_30 = rand_strided((32768, 1536), (1536, 1), device='cuda:0', dtype=torch.bfloat16)
    view_94 = rand_strided((32768, 1536), (1536, 1), device='cuda:0', dtype=torch.bfloat16)
    add_57 = rand_strided((16, 2048, 384), (786432, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    add_58 = rand_strided((16, 2048, 384), (786432, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    embedding_3 = rand_strided((16, 2048, 384), (786432, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt_21 = rand_strided((16, 2048, 1), (2048, 1, 1), device='cuda:0', dtype=torch.float32)
    view_96 = rand_strided((32768, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    view_106 = rand_strided((32768, 32), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    mm_35 = rand_strided((32768, 3), (3, 1), device='cuda:0', dtype=torch.bfloat16)
    cat_10 = rand_strided((16, 2048, 3, 128), (786432, 384, 128, 1), device='cuda:0', dtype=torch.bfloat16)
    cat_11 = rand_strided((16, 2048, 3, 128), (786432, 384, 128, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt_22 = rand_strided((16, 2048, 3, 1), (6144, 3, 1, 1), device='cuda:0', dtype=torch.float32)
    rsqrt_23 = rand_strided((16, 2048, 3, 1), (6144, 3, 1, 1), device='cuda:0', dtype=torch.float32)
    permute_56 = rand_strided((16, 3, 2048, 128), (786432, 128, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_57 = rand_strided((16, 3, 2048, 128), (786432, 128, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_58 = rand_strided((16, 3, 2048, 128), (786432, 128, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    getitem_45 = rand_strided((16, 3, 2048, 128), (786432, 128, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    getitem_46 = rand_strided((16, 3, 2048), (6144, 2048, 1), device='cuda:0', dtype=torch.float32)
    getitem_51 = rand_strided((), (), device='cuda:0', dtype=torch.int64)
    getitem_52 = rand_strided((), (), device='cuda:0', dtype=torch.int64)
    add_67 = rand_strided((16, 2048, 384), (786432, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt_24 = rand_strided((16, 2048, 1), (2048, 1, 1), device='cuda:0', dtype=torch.float32)
    view_113 = rand_strided((32768, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    mm_37 = rand_strided((32768, 1536), (1536, 1), device='cuda:0', dtype=torch.bfloat16)
    view_115 = rand_strided((32768, 1536), (1536, 1), device='cuda:0', dtype=torch.bfloat16)
    add_69 = rand_strided((16, 2048, 384), (786432, 384, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt_25 = rand_strided((16, 2048, 1), (2048, 1, 1), device='cuda:0', dtype=torch.float32)
    view_117 = rand_strided((32768, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    mm_39 = rand_strided((32768, 8192), (8192, 1), device='cuda:0', dtype=torch.bfloat16)
    amax = rand_strided((32768, 1), (1, 1), device='cuda:0', dtype=torch.float32)
    log = rand_strided((32768, 1), (1, 1), device='cuda:0', dtype=torch.float32)
    convert_element_type_185 = rand_strided((), (), device='cuda:0', dtype=torch.float32)
    permute_66 = rand_strided((8192, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_70 = rand_strided((384, 1536), (1536, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_74 = rand_strided((1536, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_78 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_86 = rand_strided((3, 32), (32, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_90 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_94 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_98 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_102 = rand_strided((384, 1536), (1536, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_106 = rand_strided((1536, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_110 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_118 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_122 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_126 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_130 = rand_strided((384, 1536), (1536, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_134 = rand_strided((1536, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_138 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_146 = rand_strided((3, 32), (32, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_150 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_154 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_158 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_162 = rand_strided((384, 1536), (1536, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_166 = rand_strided((1536, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_170 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_178 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_182 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_186 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_190 = rand_strided((384, 1536), (1536, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_194 = rand_strided((1536, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_198 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_206 = rand_strided((3, 32), (32, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_210 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_214 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_218 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_222 = rand_strided((384, 1536), (1536, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_226 = rand_strided((1536, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_230 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_238 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_242 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_246 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    tangents_1 = rand_strided((), (), device='cuda:0', dtype=torch.float32)
    fn = lambda: call([primals_1, primals_5, primals_6, primals_50, slice_2, slice_4, embedding, rsqrt, rsqrt_1, view, cat, cat_1, rsqrt_2, rsqrt_3, permute_3, permute_4, permute_5, getitem, getitem_1, getitem_6, getitem_7, add_9, rsqrt_4, view_14, mm_4, view_16, add_11, add_12, embedding_1, rsqrt_5, view_18, view_28, mm_9, cat_2, cat_3, rsqrt_6, rsqrt_7, permute_14, permute_15, permute_16, getitem_9, getitem_10, getitem_15, getitem_16, add_21, rsqrt_8, view_35, mm_11, view_37, add_23, add_24, rsqrt_9, view_39, cat_4, cat_5, rsqrt_10, rsqrt_11, permute_24, permute_25, permute_26, getitem_18, getitem_19, getitem_24, getitem_25, add_32, rsqrt_12, view_53, mm_17, view_55, add_34, add_35, embedding_2, rsqrt_13, view_57, view_67, mm_22, cat_6, cat_7, rsqrt_14, rsqrt_15, permute_35, permute_36, permute_37, getitem_27, getitem_28, getitem_33, getitem_34, add_44, rsqrt_16, view_74, mm_24, view_76, add_46, add_47, rsqrt_17, view_78, cat_8, cat_9, rsqrt_18, rsqrt_19, permute_45, permute_46, permute_47, getitem_36, getitem_37, getitem_42, getitem_43, add_55, rsqrt_20, view_92, mm_30, view_94, add_57, add_58, embedding_3, rsqrt_21, view_96, view_106, mm_35, cat_10, cat_11, rsqrt_22, rsqrt_23, permute_56, permute_57, permute_58, getitem_45, getitem_46, getitem_51, getitem_52, add_67, rsqrt_24, view_113, mm_37, view_115, add_69, rsqrt_25, view_117, mm_39, amax, log, convert_element_type_185, permute_66, permute_70, permute_74, permute_78, permute_86, permute_90, permute_94, permute_98, permute_102, permute_106, permute_110, permute_118, permute_122, permute_126, permute_130, permute_134, permute_138, permute_146, permute_150, permute_154, permute_158, permute_162, permute_166, permute_170, permute_178, permute_182, permute_186, permute_190, permute_194, permute_198, permute_206, permute_210, permute_214, permute_218, permute_222, permute_226, permute_230, permute_238, permute_242, permute_246, tangents_1])
    return print_performance(fn, times=times, repeat=repeat)


if __name__ == "__main__":
    from torch._inductor.wrapper_benchmark import compiled_module_main
    compiled_module_main('None', benchmark_compiled_module)
