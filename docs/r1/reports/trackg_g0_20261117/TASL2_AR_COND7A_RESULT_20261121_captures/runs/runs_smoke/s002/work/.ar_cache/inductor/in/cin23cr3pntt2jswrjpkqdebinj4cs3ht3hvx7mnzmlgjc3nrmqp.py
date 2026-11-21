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


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_smoke/s002/work/.ar_cache/inductor/e3/ce3sbwtpzzhg6xeoxra7mbodmoja6ufqih2aukl55puhh4pm6t3d.py
# Topologically Sorted Source Nodes: [loss, logits_1, truediv, tanh], Original ATen: [aten.nll_loss_backward, aten.nll_loss_forward, aten._to_copy, aten.div, aten.tanh, aten._log_softmax, aten._log_softmax_backward_data, aten.mul, aten.tanh_backward]
# Source node to ATen node mapping:
#   logits_1 => convert_element_type_125
#   loss => full_default, full_default_1, sub, sub_1
#   tanh => tanh
#   truediv => div
# Graph fragment:
#   %div_2 : [num_users=1] = call_function[target=torch.ops.aten.div.Tensor](args = (%tangents_1, %convert_element_type_126), kwargs = {})
#   %ne_3 : [num_users=2] = call_function[target=torch.ops.aten.ne.Scalar](args = (%unsqueeze_11, -1), kwargs = {})
#   %full_default : [num_users=1] = call_function[target=torch.ops.aten.full.default](args = ([], 0), kwargs = {dtype: torch.int64, layout: torch.strided, device: cuda:0, pin_memory: False})
#   %where_2 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%ne_3, %unsqueeze_11, %full_default), kwargs = {})
#   %scatter_upon_const_tensor : [num_users=1] = call_function[target=torch._inductor.fx_passes.post_grad.scatter_upon_const_tensor](args = (), kwargs = {shape: [32768, 8192], background_val: 0, dtype: torch.float32, dim: 1, selector: %where_2, val: -1.0})
#   %full_default_1 : [num_users=4] = call_function[target=torch.ops.aten.full.default](args = ([], 0.0), kwargs = {dtype: torch.float32, layout: torch.strided, device: cuda:0, pin_memory: False})
#   %where_3 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%ne_3, %div_2, %full_default_1), kwargs = {})
#   %mul_63 : [num_users=2] = call_function[target=torch.ops.aten.mul.Tensor](args = (%scatter_upon_const_tensor, %where_3), kwargs = {})
#   %convert_element_type_125 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%view_79, torch.float32), kwargs = {})
#   %div : [num_users=1] = call_function[target=torch.ops.aten.div.Tensor](args = (%convert_element_type_125, 15), kwargs = {})
#   %tanh : [num_users=2] = call_function[target=torch.ops.aten.tanh.default](args = (%div,), kwargs = {})
#   %sub : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (%view_80, %amax), kwargs = {})
#   %sub_1 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (%sub, %log), kwargs = {})
#   %exp_1 : [num_users=1] = call_function[target=torch.ops.aten.exp.default](args = (%sub_1,), kwargs = {})
#   %sum_4 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mul_63, [1], True), kwargs = {})
#   %mul_64 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%exp_1, %sum_4), kwargs = {})
#   %sub_2 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (%mul_63, %mul_64), kwargs = {})
#   %mul_65 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%view_82, 15), kwargs = {})
#   %mul_66 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%tanh, %tanh), kwargs = {})
#   %sub_3 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (1, %mul_66), kwargs = {})
#   %mul_67 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%mul_65, %sub_3), kwargs = {})
#   %div_3 : [num_users=1] = call_function[target=torch.ops.aten.div.Tensor](args = (%mul_67, 15), kwargs = {})
#   %convert_element_type_127 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%div_3, torch.bfloat16), kwargs = {})
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


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_smoke/s002/work/.ar_cache/inductor/d3/cd3idq2nqbhbtxtgqy7w5qskm742r6al54gp7zo3gdcb5pj7vuzf.py
# Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
# Source node to ATen node mapping:
# Graph fragment:
#   %convert_element_type_132 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mm_27, torch.float32), kwargs = {})
triton_poi_fused__to_copy_1 = async_compile.triton('triton_poi_fused__to_copy_1', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.pointwise(
    size_hints={'x': 2097152}, 
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*bf16', 'out_ptr0': '*fp32', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused__to_copy_1', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 1, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused__to_copy_1(in_ptr0, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 2097152
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (x0), None).to(tl.float32)
    tmp1 = tmp0.to(tl.float32)
    tl.store(out_ptr0 + (x0), tmp1, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_smoke/s002/work/.ar_cache/inductor/2t/c2tbgsv7chl7cm3hmrfmc5fmtf7eqw62cuatklw2lybm57hyhisn.py
# Topologically Sorted Source Nodes: [x_26], Original ATen: [aten._to_copy, aten.mul, aten.sum, aten.div, aten.pow, aten.add]
# Source node to ATen node mapping:
#   x_26 => convert_element_type_120
# Graph fragment:
#   %convert_element_type_133 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%view_84, torch.float32), kwargs = {})
#   %convert_element_type_120 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_46, torch.float32), kwargs = {})
#   %mul_68 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_133, %convert_element_type_120), kwargs = {})
#   %mul_69 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_133, %rsqrt_17), kwargs = {})
#   %sum_5 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mul_68, [2], True), kwargs = {dtype: torch.float32})
#   %div_4 : [num_users=1] = call_function[target=torch.ops.aten.div.Scalar](args = (%expand_8, 256), kwargs = {})
#   %pow_24 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_120, 1.0), kwargs = {})
#   %mul_72 : [num_users=1] = call_function[target=torch.ops.aten.mul.Scalar](args = (%pow_24, 2.0), kwargs = {})
#   %mul_73 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%div_4, %mul_72), kwargs = {})
#   %add_48 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_69, %mul_73), kwargs = {})
#   %convert_element_type_134 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_48, torch.bfloat16), kwargs = {})
triton_per_fused__to_copy_add_div_mul_pow_sum_2 = async_compile.triton('triton_per_fused__to_copy_add_div_mul_pow_sum_2', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 32768, 'r': 256},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'in_ptr1': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_div_mul_pow_sum_2', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': True, 'num_load': 3, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_div_mul_pow_sum_2(in_out_ptr0, in_ptr0, in_ptr1, xnumel, rnumel):
    xnumel = 32768
    XBLOCK: tl.constexpr = 1
    rnumel = 256
    RBLOCK: tl.constexpr = 256
    xoffset = tl.program_id(0) * XBLOCK
    xindex = tl.full([1], xoffset, tl.int32)
    xmask = tl.full([RBLOCK], True, tl.int1)
    rindex = tl.arange(0, RBLOCK)[:]
    roffset = 0
    rmask = tl.full([RBLOCK], True, tl.int1)
    r1 = rindex
    x0 = xindex
    tmp0 = tl.load(in_out_ptr0 + (r1 + 256*x0), None).to(tl.float32)
    tmp2 = tl.load(in_ptr0 + (r1 + 256*x0), None).to(tl.float32)
    tmp8 = tl.load(in_ptr1 + (x0), None, eviction_policy='evict_last')
    tmp1 = tmp0.to(tl.float32)
    tmp3 = tmp2.to(tl.float32)
    tmp4 = tmp1 * tmp3
    tmp5 = tl.broadcast_to(tmp4, [RBLOCK])
    tmp7 = triton_helpers.promote_to_tensor(tl.sum(tmp5, 0))
    tmp9 = tmp1 * tmp8
    tmp10 = -0.5
    tmp11 = tmp7 * tmp10
    tmp12 = tmp8 * tmp8
    tmp13 = tmp12 * tmp8
    tmp14 = tmp11 * tmp13
    tmp15 = 0.00390625
    tmp16 = tmp14 * tmp15
    tmp17 = 2.0
    tmp18 = tmp3 * tmp17
    tmp19 = tmp16 * tmp18
    tmp20 = tmp9 + tmp19
    tmp21 = tmp20.to(tl.float32)
    tl.store(in_out_ptr0 + (r1 + 256*x0), tmp21, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_smoke/s002/work/.ar_cache/inductor/jl/cjlws2e74kpnefh3qbtwl3ygtkmceurq46dbearlehpu2yjcv24a.py
# Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
# Source node to ATen node mapping:
# Graph fragment:
#   %convert_element_type_140 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mm_29, torch.float32), kwargs = {})
triton_poi_fused__to_copy_3 = async_compile.triton('triton_poi_fused__to_copy_3', '''
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
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused__to_copy_3', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 1, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused__to_copy_3(in_ptr0, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 262144
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (x0), None).to(tl.float32)
    tmp1 = tmp0.to(tl.float32)
    tl.store(out_ptr0 + (x0), tmp1, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_smoke/s002/work/.ar_cache/inductor/vs/cvssevbatybanlsok3agsffvhxpo5yhlhbzi54cwu4d4cjo2am4w.py
# Topologically Sorted Source Nodes: [relu_3, x_23], Original ATen: [aten._to_copy, aten.relu, aten.pow, aten.mul, aten.threshold_backward]
# Source node to ATen node mapping:
#   relu_3 => relu_3
#   x_23 => convert_element_type_115
# Graph fragment:
#   %convert_element_type_139 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%view_86, torch.float32), kwargs = {})
#   %relu_3 : [num_users=2] = call_function[target=torch.ops.aten.relu.default](args = (%view_75,), kwargs = {})
#   %convert_element_type_115 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%relu_3, torch.float32), kwargs = {})
#   %pow_25 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_115, 1.0), kwargs = {})
#   %mul_74 : [num_users=1] = call_function[target=torch.ops.aten.mul.Scalar](args = (%pow_25, 2.0), kwargs = {})
#   %mul_75 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_139, %mul_74), kwargs = {})
#   %convert_element_type_141 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul_75, torch.bfloat16), kwargs = {})
#   %le : [num_users=1] = call_function[target=torch.ops.aten.le.Scalar](args = (%relu_3, 0), kwargs = {})
#   %full_default_5 : [num_users=4] = call_function[target=torch.ops.aten.full.default](args = ([], 0.0), kwargs = {dtype: torch.bfloat16, layout: torch.strided, device: cuda:0, pin_memory: False})
#   %where_4 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%le, %full_default_5, %convert_element_type_141), kwargs = {})
triton_poi_fused__to_copy_mul_pow_relu_threshold_backward_4 = async_compile.triton('triton_poi_fused__to_copy_mul_pow_relu_threshold_backward_4', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.pointwise(
    size_hints={'x': 33554432}, 
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused__to_copy_mul_pow_relu_threshold_backward_4', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 2, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused__to_copy_mul_pow_relu_threshold_backward_4(in_out_ptr0, in_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 33554432
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


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_smoke/s002/work/.ar_cache/inductor/o5/co55vsvs2iahftfgwzcdnc6ac6mezqeuq66467rbihi2i4jvhujn.py
# Topologically Sorted Source Nodes: [rms_norm_16], Original ATen: [aten._to_copy, aten.mul, aten.sum, aten.div, aten.pow, aten.add]
# Source node to ATen node mapping:
#   rms_norm_16 => convert_element_type_110
# Graph fragment:
#   %convert_element_type_147 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%view_88, torch.float32), kwargs = {})
#   %convert_element_type_110 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_44, torch.float32), kwargs = {})
#   %mul_76 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_147, %convert_element_type_110), kwargs = {})
#   %mul_77 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_147, %rsqrt_16), kwargs = {})
#   %sum_6 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mul_76, [2], True), kwargs = {dtype: torch.float32})
#   %div_5 : [num_users=1] = call_function[target=torch.ops.aten.div.Scalar](args = (%expand_9, 256), kwargs = {})
#   %pow_27 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_110, 1.0), kwargs = {})
#   %mul_80 : [num_users=1] = call_function[target=torch.ops.aten.mul.Scalar](args = (%pow_27, 2.0), kwargs = {})
#   %mul_81 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%div_5, %mul_80), kwargs = {})
#   %add_49 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_77, %mul_81), kwargs = {})
#   %convert_element_type_148 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_49, torch.bfloat16), kwargs = {})
#   %add_50 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%convert_element_type_134, %convert_element_type_148), kwargs = {})
triton_per_fused__to_copy_add_div_mul_pow_sum_5 = async_compile.triton('triton_per_fused__to_copy_add_div_mul_pow_sum_5', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 32768, 'r': 256},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_div_mul_pow_sum_5', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': True, 'num_load': 4, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_div_mul_pow_sum_5(in_out_ptr0, in_ptr0, in_ptr1, in_ptr2, xnumel, rnumel):
    xnumel = 32768
    XBLOCK: tl.constexpr = 1
    rnumel = 256
    RBLOCK: tl.constexpr = 256
    xoffset = tl.program_id(0) * XBLOCK
    xindex = tl.full([1], xoffset, tl.int32)
    xmask = tl.full([RBLOCK], True, tl.int1)
    rindex = tl.arange(0, RBLOCK)[:]
    roffset = 0
    rmask = tl.full([RBLOCK], True, tl.int1)
    r1 = rindex
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (r1 + 256*x0), None).to(tl.float32)
    tmp2 = tl.load(in_ptr1 + (r1 + 256*x0), None).to(tl.float32)
    tmp8 = tl.load(in_out_ptr0 + (r1 + 256*x0), None).to(tl.float32)
    tmp9 = tl.load(in_ptr2 + (x0), None, eviction_policy='evict_last')
    tmp1 = tmp0.to(tl.float32)
    tmp3 = tmp2.to(tl.float32)
    tmp4 = tmp1 * tmp3
    tmp5 = tl.broadcast_to(tmp4, [RBLOCK])
    tmp7 = triton_helpers.promote_to_tensor(tl.sum(tmp5, 0))
    tmp10 = tmp1 * tmp9
    tmp11 = -0.5
    tmp12 = tmp7 * tmp11
    tmp13 = tmp9 * tmp9
    tmp14 = tmp13 * tmp9
    tmp15 = tmp12 * tmp14
    tmp16 = 0.00390625
    tmp17 = tmp15 * tmp16
    tmp18 = 2.0
    tmp19 = tmp3 * tmp18
    tmp20 = tmp17 * tmp19
    tmp21 = tmp10 + tmp20
    tmp22 = tmp21.to(tl.float32)
    tmp23 = tmp8 + tmp22
    tl.store(in_out_ptr0 + (r1 + 256*x0), tmp23, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_smoke/s002/work/.ar_cache/inductor/ql/cqlomos4cjfxffv5m5ait2ffnc5c65wyxjfknuad5ztbm3fj3gn7.py
# Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
# Source node to ATen node mapping:
# Graph fragment:
#   %convert_element_type_153 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mm_33, torch.float32), kwargs = {})
triton_poi_fused__to_copy_6 = async_compile.triton('triton_poi_fused__to_copy_6', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.pointwise(
    size_hints={'x': 65536}, 
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*bf16', 'out_ptr0': '*fp32', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused__to_copy_6', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 1, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused__to_copy_6(in_ptr0, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 65536
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (x0), None).to(tl.float32)
    tmp1 = tmp0.to(tl.float32)
    tl.store(out_ptr0 + (x0), tmp1, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_smoke/s002/work/.ar_cache/inductor/dg/cdgz7aevllbot4uzgkqhlz3ediyqubyu7b2vczlmbf5v22trijji.py
# Topologically Sorted Source Nodes: [k_17], Original ATen: [aten._to_copy, aten.mul, aten.sum]
# Source node to ATen node mapping:
#   k_17 => convert_element_type_105
# Graph fragment:
#   %convert_element_type_154 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%squeeze_2, torch.float32), kwargs = {})
#   %convert_element_type_105 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%cat_7, torch.float32), kwargs = {})
#   %mul_82 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_154, %convert_element_type_105), kwargs = {})
#   %sum_7 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mul_82, [3], True), kwargs = {dtype: torch.float32})
triton_per_fused__to_copy_mul_sum_7 = async_compile.triton('triton_per_fused__to_copy_mul_sum_7', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 65536, 'r': 128},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'out_ptr0': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_mul_sum_7', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 2, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_mul_sum_7(in_ptr0, in_ptr1, out_ptr0, xnumel, rnumel, XBLOCK : tl.constexpr):
    xnumel = 65536
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


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_smoke/s002/work/.ar_cache/inductor/sy/csylyokk4hf5u5ypg6j4ho546twkklr7235gr25fviwwi4ehikqn.py
# Topologically Sorted Source Nodes: [neg], Original ATen: [aten.mul, aten.neg, aten.add]
# Source node to ATen node mapping:
#   neg => neg
# Graph fragment:
#   %mul_94 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%slice_24, %slice_2), kwargs = {})
#   %neg : [num_users=8] = call_function[target=torch.ops.aten.neg.default](args = (%slice_4,), kwargs = {})
#   %mul_95 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%slice_24, %neg), kwargs = {})
#   %mul_96 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%slice_23, %slice_4), kwargs = {})
#   %add_53 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_94, %mul_96), kwargs = {})
#   %mul_97 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%slice_23, %slice_2), kwargs = {})
#   %add_54 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_95, %mul_97), kwargs = {})
#   %mul_98 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%slice_26, %slice_2), kwargs = {})
#   %mul_99 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%slice_26, %neg), kwargs = {})
#   %mul_100 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%slice_25, %slice_4), kwargs = {})
#   %add_56 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_98, %mul_100), kwargs = {})
#   %mul_101 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%slice_25, %slice_2), kwargs = {})
#   %add_57 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_99, %mul_101), kwargs = {})
triton_poi_fused_add_mul_neg_8 = async_compile.triton('triton_poi_fused_add_mul_neg_8', '''
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
    triton_meta={'signature': {'in_ptr0': '*bf16', 'in_ptr1': '*fp32', 'in_ptr2': '*fp32', 'in_ptr3': '*bf16', 'in_ptr4': '*bf16', 'in_ptr5': '*bf16', 'in_ptr6': '*bf16', 'in_ptr7': '*fp32', 'in_ptr8': '*fp32', 'in_ptr9': '*bf16', 'out_ptr0': '*bf16', 'out_ptr1': '*bf16', 'out_ptr2': '*bf16', 'out_ptr3': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_add_mul_neg_8', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 14, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_add_mul_neg_8(in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, in_ptr5, in_ptr6, in_ptr7, in_ptr8, in_ptr9, out_ptr0, out_ptr1, out_ptr2, out_ptr3, xnumel, XBLOCK : tl.constexpr):
    xnumel = 4194304
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = (xindex % 64)
    x4 = xindex // 64
    x2 = ((xindex // 128) % 2048)
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


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_smoke/s002/work/.ar_cache/inductor/l5/cl5fxgoojjtrmh5co3o35bazservd2p5druiqpblk2md6fid6s5r.py
# Topologically Sorted Source Nodes: [loss, sigmoid_1], Original ATen: [aten.nll_loss_forward, aten.sigmoid, aten.mul, aten.sum, aten.sigmoid_backward, aten.embedding_dense_backward]
# Source node to ATen node mapping:
#   loss => full_default_1
#   sigmoid_1 => sigmoid_1
# Graph fragment:
#   %full_default_1 : [num_users=4] = call_function[target=torch.ops.aten.full.default](args = ([], 0.0), kwargs = {dtype: torch.float32, layout: torch.strided, device: cuda:0, pin_memory: False})
#   %sigmoid_1 : [num_users=2] = call_function[target=torch.ops.aten.sigmoid.default](args = (%view_68,), kwargs = {})
#   %mul_103 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%squeeze_1, %view_66), kwargs = {})
#   %sum_9 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mul_103, [3], True), kwargs = {dtype: torch.float32})
#   %mul_104 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%squeeze_3, 2), kwargs = {})
#   %convert_element_type_159 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul_104, torch.float32), kwargs = {})
#   %convert_element_type_160 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%sigmoid_1, torch.float32), kwargs = {})
#   %sub_4 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (1, %convert_element_type_160), kwargs = {})
#   %mul_105 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_160, %sub_4), kwargs = {})
#   %mul_106 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_159, %mul_105), kwargs = {})
#   %convert_element_type_161 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul_106, torch.bfloat16), kwargs = {})
#   %convert_element_type_184 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%view_96, torch.float32), kwargs = {})
#   %where_5 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%unsqueeze_12, %full_default_1, %convert_element_type_184), kwargs = {})
triton_per_fused_embedding_dense_backward_mul_nll_loss_forward_sigmoid_sigmoid_backward_sum_9 = async_compile.triton('triton_per_fused_embedding_dense_backward_mul_nll_loss_forward_sigmoid_sigmoid_backward_sum_9', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 65536, 'r': 128},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*i64', 'in_ptr3': '*bf16', 'out_ptr1': '*fp32', 'out_ptr2': '*bf16', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused_embedding_dense_backward_mul_nll_loss_forward_sigmoid_sigmoid_backward_sum_9', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 5, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused_embedding_dense_backward_mul_nll_loss_forward_sigmoid_sigmoid_backward_sum_9(in_ptr0, in_ptr1, in_ptr2, in_ptr3, out_ptr1, out_ptr2, xnumel, rnumel, XBLOCK : tl.constexpr):
    xnumel = 65536
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
    x3 = xindex // 2
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


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_smoke/s002/work/.ar_cache/inductor/uj/cujury6vgkpdm5fkge7e7ekicuinsbiskfcdij3l7teoeump6lwa.py
# Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
# Source node to ATen node mapping:
# Graph fragment:
#   %convert_element_type_166 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mm_35, torch.float32), kwargs = {})
triton_poi_fused__to_copy_10 = async_compile.triton('triton_poi_fused__to_copy_10', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.pointwise(
    size_hints={'x': 64}, 
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*bf16', 'out_ptr0': '*fp32', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused__to_copy_10', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 1, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused__to_copy_10(in_ptr0, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 64
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = xindex < xnumel
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (x0), xmask).to(tl.float32)
    tmp1 = tmp0.to(tl.float32)
    tl.store(out_ptr0 + (x0), tmp1, xmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_smoke/s002/work/.ar_cache/inductor/c7/cc7nqjkwjtunj7jaf3db34ag2henqfrejqv5ot3k2pkagzllavpn.py
# Topologically Sorted Source Nodes: [], Original ATen: [aten.slice_backward, aten.add]
# Source node to ATen node mapping:
# Graph fragment:
#   %full_default_6 : [num_users=16] = call_function[target=torch.ops.aten.full.default](args = ([16, 2048, 2, 128], 0), kwargs = {dtype: torch.bfloat16, layout: torch.strided, device: cuda:0, pin_memory: False})
#   %slice_scatter_default : [num_users=1] = call_function[target=torch.ops.aten.slice_scatter.default](args = (%full_default_6, %add_53, 3, 64, 9223372036854775807), kwargs = {})
#   %slice_scatter_default_1 : [num_users=1] = call_function[target=torch.ops.aten.slice_scatter.default](args = (%full_default_6, %add_54, 3, 0, 64), kwargs = {})
#   %add_55 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%slice_scatter_default, %slice_scatter_default_1), kwargs = {})
triton_poi_fused_add_slice_backward_11 = async_compile.triton('triton_poi_fused_add_slice_backward_11', '''
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
    triton_meta={'signature': {'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'out_ptr0': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_add_slice_backward_11', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 2, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_add_slice_backward_11(in_ptr0, in_ptr1, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 8388608
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


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_smoke/s002/work/.ar_cache/inductor/k7/ck7cikbhdsjv3c3c3xovysapg67nenxyvah224yu3q4ti7symjmm.py
# Topologically Sorted Source Nodes: [rms_norm_13], Original ATen: [aten.slice_backward, aten.add, aten._to_copy, aten.mul, aten.sum, aten.div, aten.pow]
# Source node to ATen node mapping:
#   rms_norm_13 => convert_element_type_89
# Graph fragment:
#   %full_default_10 : [num_users=2] = call_function[target=torch.ops.aten.full.default](args = ([16, 2048, 256], 0), kwargs = {dtype: torch.bfloat16, layout: torch.strided, device: cuda:0, pin_memory: False})
#   %slice_scatter_default_4 : [num_users=1] = call_function[target=torch.ops.aten.slice_scatter.default](args = (%full_default_10, %view_95, 2, 0, 32), kwargs = {})
#   %add_59 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%slice_scatter_default_4, %view_99), kwargs = {})
#   %add_60 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_59, %view_102), kwargs = {})
#   %add_61 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_60, %view_105), kwargs = {})
#   %convert_element_type_182 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_61, torch.float32), kwargs = {})
#   %convert_element_type_89 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_35, torch.float32), kwargs = {})
#   %mul_107 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_182, %convert_element_type_89), kwargs = {})
#   %mul_108 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_182, %rsqrt_13), kwargs = {})
#   %sum_10 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mul_107, [2], True), kwargs = {dtype: torch.float32})
#   %div_8 : [num_users=1] = call_function[target=torch.ops.aten.div.Scalar](args = (%expand_12, 256), kwargs = {})
#   %pow_33 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_89, 1.0), kwargs = {})
#   %mul_111 : [num_users=1] = call_function[target=torch.ops.aten.mul.Scalar](args = (%pow_33, 2.0), kwargs = {})
#   %mul_112 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%div_8, %mul_111), kwargs = {})
#   %add_62 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_108, %mul_112), kwargs = {})
#   %convert_element_type_183 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_62, torch.bfloat16), kwargs = {})
#   %add_63 : [num_users=4] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_50, %convert_element_type_183), kwargs = {})
#   %mul_115 : [num_users=2] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_63, %select_6), kwargs = {})
triton_red_fused__to_copy_add_div_mul_pow_slice_backward_sum_12 = async_compile.triton('triton_red_fused__to_copy_add_div_mul_pow_slice_backward_sum_12', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.reduction(
    size_hints={'x': 32768, 'r': 256},
    reduction_hint=ReductionHint.DEFAULT,
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'in_ptr3': '*bf16', 'in_ptr4': '*fp32', 'in_ptr5': '*bf16', 'in_ptr6': '*fp32', 'out_ptr1': '*bf16', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_red_fused__to_copy_add_div_mul_pow_slice_backward_sum_12', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 13, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_red_fused__to_copy_add_div_mul_pow_slice_backward_sum_12(in_out_ptr0, in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, in_ptr5, in_ptr6, out_ptr1, xnumel, rnumel, XBLOCK : tl.constexpr, RBLOCK : tl.constexpr):
    xnumel = 32768
    rnumel = 256
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
        tmp6 = tl.load(in_out_ptr0 + (r1 + 256*x0), rmask, eviction_policy='evict_last', other=0.0).to(tl.float32)
        tmp8 = tl.load(in_ptr1 + (r1 + 256*x0), rmask, eviction_policy='evict_last', other=0.0).to(tl.float32)
        tmp10 = tl.load(in_ptr2 + (r1 + 256*x0), rmask, eviction_policy='evict_last', other=0.0).to(tl.float32)
        tmp13 = tl.load(in_ptr3 + (r1 + 256*x0), rmask, eviction_policy='evict_last', other=0.0).to(tl.float32)
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
        tmp25 = tl.load(in_out_ptr0 + (r1 + 256*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp27 = tl.load(in_ptr1 + (r1 + 256*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp29 = tl.load(in_ptr2 + (r1 + 256*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp41 = tl.load(in_ptr3 + (r1 + 256*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp48 = tl.load(in_ptr5 + (r1 + 256*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
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
        tmp39 = 0.00390625
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
        tl.store(in_out_ptr0 + (r1 + 256*x0), tmp47, rmask)
        tl.store(out_ptr1 + (r1 + 256*x0), tmp53, rmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_smoke/s002/work/.ar_cache/inductor/qb/cqb4aakyw3kyuo7gplegrrguo6gbifewbz6kdu3lqq46gruvi77w.py
# Topologically Sorted Source Nodes: [loss], Original ATen: [aten.nll_loss_forward, aten.embedding_dense_backward]
# Source node to ATen node mapping:
#   loss => full_default_1
# Graph fragment:
#   %full_default_1 : [num_users=4] = call_function[target=torch.ops.aten.full.default](args = ([], 0.0), kwargs = {dtype: torch.float32, layout: torch.strided, device: cuda:0, pin_memory: False})
#   %convert_element_type_184 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%view_96, torch.float32), kwargs = {})
#   %where_5 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%unsqueeze_12, %full_default_1, %convert_element_type_184), kwargs = {})
#   %full_default_12 : [num_users=3] = call_function[target=torch.ops.aten.full.default](args = ([8192, 256], 0), kwargs = {dtype: torch.float32, layout: torch.strided, device: cuda:0, pin_memory: False})
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
    size_hints={'x': 2097152}, 
    filename=__file__,
    triton_meta={'signature': {'out_ptr0': '*fp32', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_embedding_dense_backward_nll_loss_forward_13', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 0, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_embedding_dense_backward_nll_loss_forward_13(out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 2097152
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = xindex
    tmp0 = 0.0
    tl.store(out_ptr0 + (x0), tmp0, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_smoke/s002/work/.ar_cache/inductor/fk/cfkndi6j37abgkpfszv6qjm22gxha243beawz5vmelw2wyspeprk.py
# Topologically Sorted Source Nodes: [], Original ATen: [aten.embedding_dense_backward]
# Source node to ATen node mapping:
# Graph fragment:
#   %convert_element_type_185 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%index_put, torch.bfloat16), kwargs = {})
triton_poi_fused_embedding_dense_backward_14 = async_compile.triton('triton_poi_fused_embedding_dense_backward_14', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.pointwise(
    size_hints={'x': 2097152}, 
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*fp32', 'out_ptr0': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_embedding_dense_backward_14', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 1, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_embedding_dense_backward_14(in_ptr0, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 2097152
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (x0), None)
    tmp1 = tmp0.to(tl.float32)
    tl.store(out_ptr0 + (x0), tmp1, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_smoke/s002/work/.ar_cache/inductor/dk/cdkjg6xuaxusswlmxoa65zbj7ay42ndsdvj7p3wc6qysfbfltyyy.py
# Topologically Sorted Source Nodes: [rms_norm_12], Original ATen: [aten._to_copy, aten.mul, aten.sum, aten.div, aten.pow, aten.add]
# Source node to ATen node mapping:
#   rms_norm_12 => convert_element_type_79
# Graph fragment:
#   %convert_element_type_198 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%view_109, torch.float32), kwargs = {})
#   %convert_element_type_79 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_32, torch.float32), kwargs = {})
#   %mul_119 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_198, %convert_element_type_79), kwargs = {})
#   %mul_120 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_198, %rsqrt_12), kwargs = {})
#   %sum_13 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mul_119, [2], True), kwargs = {dtype: torch.float32})
#   %div_9 : [num_users=1] = call_function[target=torch.ops.aten.div.Scalar](args = (%expand_13, 256), kwargs = {})
#   %pow_36 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_79, 1.0), kwargs = {})
#   %mul_123 : [num_users=1] = call_function[target=torch.ops.aten.mul.Scalar](args = (%pow_36, 2.0), kwargs = {})
#   %mul_124 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%div_9, %mul_123), kwargs = {})
#   %add_64 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_120, %mul_124), kwargs = {})
#   %convert_element_type_199 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_64, torch.bfloat16), kwargs = {})
#   %add_65 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_115, %convert_element_type_199), kwargs = {})
triton_per_fused__to_copy_add_div_mul_pow_sum_15 = async_compile.triton('triton_per_fused__to_copy_add_div_mul_pow_sum_15', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 32768, 'r': 256},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_div_mul_pow_sum_15', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': True, 'num_load': 4, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_div_mul_pow_sum_15(in_out_ptr0, in_ptr0, in_ptr1, in_ptr2, xnumel, rnumel):
    xnumel = 32768
    XBLOCK: tl.constexpr = 1
    rnumel = 256
    RBLOCK: tl.constexpr = 256
    xoffset = tl.program_id(0) * XBLOCK
    xindex = tl.full([1], xoffset, tl.int32)
    xmask = tl.full([RBLOCK], True, tl.int1)
    rindex = tl.arange(0, RBLOCK)[:]
    roffset = 0
    rmask = tl.full([RBLOCK], True, tl.int1)
    r1 = rindex
    x0 = xindex
    tmp0 = tl.load(in_out_ptr0 + (r1 + 256*x0), None).to(tl.float32)
    tmp2 = tl.load(in_ptr0 + (r1 + 256*x0), None).to(tl.float32)
    tmp8 = tl.load(in_ptr1 + (r1 + 256*x0), None).to(tl.float32)
    tmp9 = tl.load(in_ptr2 + (x0), None, eviction_policy='evict_last')
    tmp1 = tmp0.to(tl.float32)
    tmp3 = tmp2.to(tl.float32)
    tmp4 = tmp1 * tmp3
    tmp5 = tl.broadcast_to(tmp4, [RBLOCK])
    tmp7 = triton_helpers.promote_to_tensor(tl.sum(tmp5, 0))
    tmp10 = tmp1 * tmp9
    tmp11 = -0.5
    tmp12 = tmp7 * tmp11
    tmp13 = tmp9 * tmp9
    tmp14 = tmp13 * tmp9
    tmp15 = tmp12 * tmp14
    tmp16 = 0.00390625
    tmp17 = tmp15 * tmp16
    tmp18 = 2.0
    tmp19 = tmp3 * tmp18
    tmp20 = tmp17 * tmp19
    tmp21 = tmp10 + tmp20
    tmp22 = tmp21.to(tl.float32)
    tmp23 = tmp8 + tmp22
    tl.store(in_out_ptr0 + (r1 + 256*x0), tmp23, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_smoke/s002/work/.ar_cache/inductor/t7/ct72c3ykul5pfudpc3cysbhatttyf6y5flii62c7xf3fg7vesrws.py
# Topologically Sorted Source Nodes: [x_1, rms_norm_9], Original ATen: [aten.add, aten._to_copy, aten.mul, aten.sum, aten.div, aten.pow, aten.view]
# Source node to ATen node mapping:
#   rms_norm_9 => convert_element_type_61
#   x_1 => convert_element_type, convert_element_type_1, mul
# Graph fragment:
#   %add_63 : [num_users=4] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_50, %convert_element_type_183), kwargs = {})
#   %convert_element_type : [num_users=3] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%embedding, torch.float32), kwargs = {})
#   %mul : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type, %rsqrt), kwargs = {})
#   %convert_element_type_1 : [num_users=6] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul, torch.bfloat16), kwargs = {})
#   %mul_114 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_63, %convert_element_type_1), kwargs = {})
#   %sum_11 : [num_users=1] = call_function[target=torch.ops.aten.sum.default](args = (%mul_114,), kwargs = {dtype: torch.float32})
#   %mul_116 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_63, %add_34), kwargs = {})
#   %sum_12 : [num_users=1] = call_function[target=torch.ops.aten.sum.default](args = (%mul_116,), kwargs = {dtype: torch.float32})
#   %add_74 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%view_117, %view_120), kwargs = {})
#   %add_75 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_74, %view_123), kwargs = {})
#   %convert_element_type_224 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_75, torch.float32), kwargs = {})
#   %convert_element_type_61 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_24, torch.float32), kwargs = {})
#   %mul_145 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_224, %convert_element_type_61), kwargs = {})
#   %mul_146 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_224, %rsqrt_9), kwargs = {})
#   %sum_16 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mul_145, [2], True), kwargs = {dtype: torch.float32})
#   %div_12 : [num_users=1] = call_function[target=torch.ops.aten.div.Scalar](args = (%expand_16, 256), kwargs = {})
#   %pow_42 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_61, 1.0), kwargs = {})
#   %mul_149 : [num_users=1] = call_function[target=torch.ops.aten.mul.Scalar](args = (%pow_42, 2.0), kwargs = {})
#   %mul_150 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%div_12, %mul_149), kwargs = {})
#   %add_76 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_146, %mul_150), kwargs = {})
#   %convert_element_type_225 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_76, torch.bfloat16), kwargs = {})
#   %add_77 : [num_users=4] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_65, %convert_element_type_225), kwargs = {})
#   %mul_152 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_77, %convert_element_type_1), kwargs = {})
#   %sum_17 : [num_users=1] = call_function[target=torch.ops.aten.sum.default](args = (%mul_152,), kwargs = {dtype: torch.float32})
#   %mul_153 : [num_users=2] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_77, %select_4), kwargs = {})
#   %mul_154 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_77, %add_23), kwargs = {})
#   %sum_18 : [num_users=1] = call_function[target=torch.ops.aten.sum.default](args = (%mul_154,), kwargs = {dtype: torch.float32})
#   %view_124 : [num_users=2] = call_function[target=torch.ops.aten.reshape.default](args = (%mul_153, [32768, 256]), kwargs = {})
triton_per_fused__to_copy_add_div_mul_pow_sum_view_16 = async_compile.triton('triton_per_fused__to_copy_add_div_mul_pow_sum_view_16', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 32768, 'r': 256},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'in_ptr3': '*bf16', 'in_ptr4': '*fp32', 'in_ptr5': '*fp32', 'in_ptr6': '*bf16', 'in_ptr7': '*bf16', 'in_ptr8': '*bf16', 'in_ptr9': '*fp32', 'in_ptr10': '*bf16', 'in_ptr11': '*bf16', 'out_ptr1': '*bf16', 'out_ptr2': '*fp32', 'out_ptr3': '*fp32', 'out_ptr4': '*fp32', 'out_ptr5': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_div_mul_pow_sum_view_16', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': True, 'num_load': 13, 'num_reduction': 5, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_div_mul_pow_sum_view_16(in_out_ptr0, in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, in_ptr5, in_ptr6, in_ptr7, in_ptr8, in_ptr9, in_ptr10, in_ptr11, out_ptr1, out_ptr2, out_ptr3, out_ptr4, out_ptr5, xnumel, rnumel):
    xnumel = 32768
    XBLOCK: tl.constexpr = 1
    rnumel = 256
    RBLOCK: tl.constexpr = 256
    xoffset = tl.program_id(0) * XBLOCK
    xindex = tl.full([1], xoffset, tl.int32)
    xmask = tl.full([RBLOCK], True, tl.int1)
    rindex = tl.arange(0, RBLOCK)[:]
    roffset = 0
    rmask = tl.full([RBLOCK], True, tl.int1)
    r1 = rindex
    x0 = xindex
    tmp0 = tl.load(in_out_ptr0 + (r1 + 256*x0), None).to(tl.float32)
    tmp1 = tl.load(in_ptr0 + (r1 + 256*x0), None).to(tl.float32)
    tmp3 = tl.load(in_ptr1 + (r1 + 256*x0), None).to(tl.float32)
    tmp6 = tl.load(in_ptr2 + (r1 + 256*x0), None).to(tl.float32)
    tmp12 = tl.load(in_ptr3 + (r1 + 256*x0), None).to(tl.float32)
    tmp13 = tl.load(in_ptr4 + (x0), None, eviction_policy='evict_last')
    tmp28 = tl.load(in_ptr5 + (2))
    tmp29 = tl.broadcast_to(tmp28, [RBLOCK])
    tmp32 = tl.load(in_ptr6 + (r1 + 256*x0), None).to(tl.float32)
    tmp33 = tl.load(in_ptr7 + (r1 + 256*x0), None).to(tl.float32)
    tmp35 = tl.load(in_ptr8 + (r1 + 256*x0), None).to(tl.float32)
    tmp37 = tl.load(in_ptr9 + (x0), None, eviction_policy='evict_last')
    tmp45 = tl.load(in_ptr10 + (r1 + 256*x0), None).to(tl.float32)
    tmp56 = tl.load(in_ptr11 + (r1 + 256*x0), None).to(tl.float32)
    tmp2 = tmp0 + tmp1
    tmp4 = tmp2 + tmp3
    tmp5 = tmp4.to(tl.float32)
    tmp7 = tmp6.to(tl.float32)
    tmp8 = tmp5 * tmp7
    tmp9 = tl.broadcast_to(tmp8, [RBLOCK])
    tmp11 = triton_helpers.promote_to_tensor(tl.sum(tmp9, 0))
    tmp14 = tmp5 * tmp13
    tmp15 = -0.5
    tmp16 = tmp11 * tmp15
    tmp17 = tmp13 * tmp13
    tmp18 = tmp17 * tmp13
    tmp19 = tmp16 * tmp18
    tmp20 = 0.00390625
    tmp21 = tmp19 * tmp20
    tmp22 = 2.0
    tmp23 = tmp7 * tmp22
    tmp24 = tmp21 * tmp23
    tmp25 = tmp14 + tmp24
    tmp26 = tmp25.to(tl.float32)
    tmp27 = tmp12 + tmp26
    tmp30 = tmp29.to(tl.float32)
    tmp31 = tmp27 * tmp30
    tmp34 = tmp32 + tmp33
    tmp36 = tmp35.to(tl.float32)
    tmp38 = tmp36 * tmp37
    tmp39 = tmp38.to(tl.float32)
    tmp40 = tmp34 * tmp39
    tmp41 = tmp40.to(tl.float32)
    tmp42 = tl.broadcast_to(tmp41, [RBLOCK])
    tmp44 = triton_helpers.promote_to_tensor(tl.sum(tmp42, 0))
    tmp46 = tmp34 * tmp45
    tmp47 = tmp46.to(tl.float32)
    tmp48 = tl.broadcast_to(tmp47, [RBLOCK])
    tmp50 = triton_helpers.promote_to_tensor(tl.sum(tmp48, 0))
    tmp51 = tmp27 * tmp39
    tmp52 = tmp51.to(tl.float32)
    tmp53 = tl.broadcast_to(tmp52, [RBLOCK])
    tmp55 = triton_helpers.promote_to_tensor(tl.sum(tmp53, 0))
    tmp57 = tmp27 * tmp56
    tmp58 = tmp57.to(tl.float32)
    tmp59 = tl.broadcast_to(tmp58, [RBLOCK])
    tmp61 = triton_helpers.promote_to_tensor(tl.sum(tmp59, 0))
    tl.store(in_out_ptr0 + (r1 + 256*x0), tmp27, None)
    tl.store(out_ptr1 + (r1 + 256*x0), tmp31, None)
    tl.store(out_ptr2 + (x0), tmp44, None)
    tl.store(out_ptr3 + (x0), tmp50, None)
    tl.store(out_ptr4 + (x0), tmp55, None)
    tl.store(out_ptr5 + (x0), tmp61, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_smoke/s002/work/.ar_cache/inductor/zl/czl3qqfvuvjwws2f6oqbe4q3636z6zgpipxex4glu7ljea35gb32.py
# Topologically Sorted Source Nodes: [x_1], Original ATen: [aten.add, aten._to_copy, aten.mul, aten.sum]
# Source node to ATen node mapping:
#   x_1 => convert_element_type, convert_element_type_1, mul
# Graph fragment:
#   %add_63 : [num_users=4] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_50, %convert_element_type_183), kwargs = {})
#   %convert_element_type : [num_users=3] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%embedding, torch.float32), kwargs = {})
#   %mul : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type, %rsqrt), kwargs = {})
#   %convert_element_type_1 : [num_users=6] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul, torch.bfloat16), kwargs = {})
#   %mul_114 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_63, %convert_element_type_1), kwargs = {})
#   %sum_11 : [num_users=1] = call_function[target=torch.ops.aten.sum.default](args = (%mul_114,), kwargs = {dtype: torch.float32})
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


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_smoke/s002/work/.ar_cache/inductor/7a/c7anngw5ermudj63sz6ni2ojnfpvwvnhvy6sh67trv354v3gfxli.py
# Topologically Sorted Source Nodes: [rms_norm_8], Original ATen: [aten.mul, aten._to_copy, aten.sum, aten.div, aten.pow, aten.add]
# Source node to ATen node mapping:
#   rms_norm_8 => convert_element_type_51
# Graph fragment:
#   %mul_153 : [num_users=2] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_77, %select_4), kwargs = {})
#   %convert_element_type_238 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%view_127, torch.float32), kwargs = {})
#   %convert_element_type_51 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_21, torch.float32), kwargs = {})
#   %mul_157 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_238, %convert_element_type_51), kwargs = {})
#   %mul_158 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_238, %rsqrt_8), kwargs = {})
#   %sum_19 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mul_157, [2], True), kwargs = {dtype: torch.float32})
#   %div_13 : [num_users=1] = call_function[target=torch.ops.aten.div.Scalar](args = (%expand_17, 256), kwargs = {})
#   %pow_45 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_51, 1.0), kwargs = {})
#   %mul_161 : [num_users=1] = call_function[target=torch.ops.aten.mul.Scalar](args = (%pow_45, 2.0), kwargs = {})
#   %mul_162 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%div_13, %mul_161), kwargs = {})
#   %add_81 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_158, %mul_162), kwargs = {})
#   %convert_element_type_239 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_81, torch.bfloat16), kwargs = {})
#   %add_82 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_153, %convert_element_type_239), kwargs = {})
triton_per_fused__to_copy_add_div_mul_pow_sum_18 = async_compile.triton('triton_per_fused__to_copy_add_div_mul_pow_sum_18', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 32768, 'r': 256},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*fp32', 'in_ptr3': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_div_mul_pow_sum_18', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': True, 'num_load': 5, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_div_mul_pow_sum_18(in_out_ptr0, in_ptr0, in_ptr1, in_ptr2, in_ptr3, xnumel, rnumel):
    xnumel = 32768
    XBLOCK: tl.constexpr = 1
    rnumel = 256
    RBLOCK: tl.constexpr = 256
    xoffset = tl.program_id(0) * XBLOCK
    xindex = tl.full([1], xoffset, tl.int32)
    xmask = tl.full([RBLOCK], True, tl.int1)
    rindex = tl.arange(0, RBLOCK)[:]
    roffset = 0
    rmask = tl.full([RBLOCK], True, tl.int1)
    r1 = rindex
    x0 = xindex
    tmp0 = tl.load(in_out_ptr0 + (r1 + 256*x0), None).to(tl.float32)
    tmp2 = tl.load(in_ptr0 + (r1 + 256*x0), None).to(tl.float32)
    tmp8 = tl.load(in_ptr1 + (r1 + 256*x0), None).to(tl.float32)
    tmp9 = tl.load(in_ptr2 + (2))
    tmp10 = tl.broadcast_to(tmp9, [RBLOCK])
    tmp13 = tl.load(in_ptr3 + (x0), None, eviction_policy='evict_last')
    tmp1 = tmp0.to(tl.float32)
    tmp3 = tmp2.to(tl.float32)
    tmp4 = tmp1 * tmp3
    tmp5 = tl.broadcast_to(tmp4, [RBLOCK])
    tmp7 = triton_helpers.promote_to_tensor(tl.sum(tmp5, 0))
    tmp11 = tmp10.to(tl.float32)
    tmp12 = tmp8 * tmp11
    tmp14 = tmp1 * tmp13
    tmp15 = -0.5
    tmp16 = tmp7 * tmp15
    tmp17 = tmp13 * tmp13
    tmp18 = tmp17 * tmp13
    tmp19 = tmp16 * tmp18
    tmp20 = 0.00390625
    tmp21 = tmp19 * tmp20
    tmp22 = 2.0
    tmp23 = tmp3 * tmp22
    tmp24 = tmp21 * tmp23
    tmp25 = tmp14 + tmp24
    tmp26 = tmp25.to(tl.float32)
    tmp27 = tmp12 + tmp26
    tl.store(in_out_ptr0 + (r1 + 256*x0), tmp27, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_smoke/s002/work/.ar_cache/inductor/dm/cdmybla77j7loncrz43riliqhb6yc5iiryddlmuqwb5u4wd5ocsm.py
# Topologically Sorted Source Nodes: [sigmoid], Original ATen: [aten.sigmoid, aten.mul, aten.sum, aten.sigmoid_backward]
# Source node to ATen node mapping:
#   sigmoid => sigmoid
# Graph fragment:
#   %sigmoid : [num_users=2] = call_function[target=torch.ops.aten.sigmoid.default](args = (%view_29,), kwargs = {})
#   %mul_184 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%squeeze_6, %view_27), kwargs = {})
#   %sum_22 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mul_184, [3], True), kwargs = {dtype: torch.float32})
#   %mul_185 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%squeeze_8, 2), kwargs = {})
#   %convert_element_type_250 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul_185, torch.float32), kwargs = {})
#   %convert_element_type_251 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%sigmoid, torch.float32), kwargs = {})
#   %sub_5 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (1, %convert_element_type_251), kwargs = {})
#   %mul_186 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_251, %sub_5), kwargs = {})
#   %mul_187 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_250, %mul_186), kwargs = {})
#   %convert_element_type_252 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul_187, torch.bfloat16), kwargs = {})
triton_per_fused_mul_sigmoid_sigmoid_backward_sum_19 = async_compile.triton('triton_per_fused_mul_sigmoid_sigmoid_backward_sum_19', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 65536, 'r': 128},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'out_ptr1': '*bf16', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused_mul_sigmoid_sigmoid_backward_sum_19', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 3, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused_mul_sigmoid_sigmoid_backward_sum_19(in_ptr0, in_ptr1, in_ptr2, out_ptr1, xnumel, rnumel, XBLOCK : tl.constexpr):
    xnumel = 65536
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


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_smoke/s002/work/.ar_cache/inductor/v2/cv2tl5gve6lqsctcqjjxhstfhe7f2hshizycejcs6qqega4hvxgk.py
# Topologically Sorted Source Nodes: [rms_norm_5], Original ATen: [aten.slice_backward, aten.add, aten._to_copy, aten.mul, aten.sum, aten.div, aten.pow]
# Source node to ATen node mapping:
#   rms_norm_5 => convert_element_type_30
# Graph fragment:
#   %full_default_10 : [num_users=2] = call_function[target=torch.ops.aten.full.default](args = ([16, 2048, 256], 0), kwargs = {dtype: torch.bfloat16, layout: torch.strided, device: cuda:0, pin_memory: False})
#   %slice_scatter_default_13 : [num_users=1] = call_function[target=torch.ops.aten.slice_scatter.default](args = (%full_default_10, %view_134, 2, 0, 32), kwargs = {})
#   %add_91 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%slice_scatter_default_13, %view_138), kwargs = {})
#   %add_92 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_91, %view_141), kwargs = {})
#   %add_93 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_92, %view_144), kwargs = {})
#   %convert_element_type_273 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_93, torch.float32), kwargs = {})
#   %convert_element_type_30 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_12, torch.float32), kwargs = {})
#   %mul_188 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_273, %convert_element_type_30), kwargs = {})
#   %mul_189 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_273, %rsqrt_5), kwargs = {})
#   %sum_23 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mul_188, [2], True), kwargs = {dtype: torch.float32})
#   %div_16 : [num_users=1] = call_function[target=torch.ops.aten.div.Scalar](args = (%expand_20, 256), kwargs = {})
#   %pow_51 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_30, 1.0), kwargs = {})
#   %mul_192 : [num_users=1] = call_function[target=torch.ops.aten.mul.Scalar](args = (%pow_51, 2.0), kwargs = {})
#   %mul_193 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%div_16, %mul_192), kwargs = {})
#   %add_94 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_189, %mul_193), kwargs = {})
#   %convert_element_type_274 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_94, torch.bfloat16), kwargs = {})
#   %add_95 : [num_users=4] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_82, %convert_element_type_274), kwargs = {})
#   %mul_196 : [num_users=2] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_95, %select_2), kwargs = {})
triton_red_fused__to_copy_add_div_mul_pow_slice_backward_sum_20 = async_compile.triton('triton_red_fused__to_copy_add_div_mul_pow_slice_backward_sum_20', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.reduction(
    size_hints={'x': 32768, 'r': 256},
    reduction_hint=ReductionHint.DEFAULT,
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'in_ptr3': '*bf16', 'in_ptr4': '*fp32', 'in_ptr5': '*bf16', 'in_ptr6': '*fp32', 'out_ptr1': '*bf16', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_red_fused__to_copy_add_div_mul_pow_slice_backward_sum_20', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 13, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_red_fused__to_copy_add_div_mul_pow_slice_backward_sum_20(in_out_ptr0, in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, in_ptr5, in_ptr6, out_ptr1, xnumel, rnumel, XBLOCK : tl.constexpr, RBLOCK : tl.constexpr):
    xnumel = 32768
    rnumel = 256
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
        tmp6 = tl.load(in_out_ptr0 + (r1 + 256*x0), rmask, eviction_policy='evict_last', other=0.0).to(tl.float32)
        tmp8 = tl.load(in_ptr1 + (r1 + 256*x0), rmask, eviction_policy='evict_last', other=0.0).to(tl.float32)
        tmp10 = tl.load(in_ptr2 + (r1 + 256*x0), rmask, eviction_policy='evict_last', other=0.0).to(tl.float32)
        tmp13 = tl.load(in_ptr3 + (r1 + 256*x0), rmask, eviction_policy='evict_last', other=0.0).to(tl.float32)
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
        tmp25 = tl.load(in_out_ptr0 + (r1 + 256*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp27 = tl.load(in_ptr1 + (r1 + 256*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp29 = tl.load(in_ptr2 + (r1 + 256*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp41 = tl.load(in_ptr3 + (r1 + 256*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp48 = tl.load(in_ptr5 + (r1 + 256*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
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
        tmp39 = 0.00390625
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
        tl.store(in_out_ptr0 + (r1 + 256*x0), tmp47, rmask)
        tl.store(out_ptr1 + (r1 + 256*x0), tmp53, rmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_smoke/s002/work/.ar_cache/inductor/75/c75tqqoor6egyrrncj7utzl2vvyaxunkn5x2ndik6jmqdhnmsujo.py
# Topologically Sorted Source Nodes: [loss, x_1, mul, mul_1, x_2, rms_norm_1], Original ATen: [aten.nll_loss_forward, aten.add, aten.mul, aten._to_copy, aten.embedding_dense_backward, aten.sum, aten.div, aten.pow]
# Source node to ATen node mapping:
#   loss => full_default_1
#   mul => mul_1
#   mul_1 => mul_2
#   rms_norm_1 => convert_element_type_2
#   x_1 => convert_element_type, convert_element_type_1, mul
#   x_2 => add_1
# Graph fragment:
#   %full_default_1 : [num_users=4] = call_function[target=torch.ops.aten.full.default](args = ([], 0.0), kwargs = {dtype: torch.float32, layout: torch.strided, device: cuda:0, pin_memory: False})
#   %add_63 : [num_users=4] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_50, %convert_element_type_183), kwargs = {})
#   %mul_113 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_63, %select_7), kwargs = {})
#   %convert_element_type : [num_users=3] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%embedding, torch.float32), kwargs = {})
#   %mul : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type, %rsqrt), kwargs = {})
#   %convert_element_type_1 : [num_users=6] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul, torch.bfloat16), kwargs = {})
#   %mul_151 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_77, %select_5), kwargs = {})
#   %add_78 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_113, %mul_151), kwargs = {})
#   %add_95 : [num_users=4] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_82, %convert_element_type_274), kwargs = {})
#   %convert_element_type_275 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%view_135, torch.float32), kwargs = {})
#   %where_8 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%unsqueeze_12, %full_default_1, %convert_element_type_275), kwargs = {})
#   %mul_194 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_95, %select_3), kwargs = {})
#   %mul_195 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_95, %convert_element_type_1), kwargs = {})
#   %sum_24 : [num_users=1] = call_function[target=torch.ops.aten.sum.default](args = (%mul_195,), kwargs = {dtype: torch.float32})
#   %add_96 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_78, %mul_194), kwargs = {})
#   %mul_197 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_95, %add_11), kwargs = {})
#   %sum_25 : [num_users=1] = call_function[target=torch.ops.aten.sum.default](args = (%mul_197,), kwargs = {dtype: torch.float32})
#   %add_109 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%view_156, %view_159), kwargs = {})
#   %add_110 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_109, %view_162), kwargs = {})
#   %convert_element_type_315 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_110, torch.float32), kwargs = {})
#   %mul_1 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%select, %convert_element_type_1), kwargs = {})
#   %mul_2 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%select_1, %convert_element_type_1), kwargs = {})
#   %add_1 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_1, %mul_2), kwargs = {})
#   %convert_element_type_2 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_1, torch.float32), kwargs = {})
#   %mul_226 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_315, %convert_element_type_2), kwargs = {})
#   %mul_227 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_315, %rsqrt_1), kwargs = {})
#   %sum_29 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mul_226, [2], True), kwargs = {dtype: torch.float32})
#   %div_20 : [num_users=1] = call_function[target=torch.ops.aten.div.Scalar](args = (%expand_24, 256), kwargs = {})
#   %pow_60 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_2, 1.0), kwargs = {})
#   %mul_230 : [num_users=1] = call_function[target=torch.ops.aten.mul.Scalar](args = (%pow_60, 2.0), kwargs = {})
#   %mul_231 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%div_20, %mul_230), kwargs = {})
#   %add_111 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_227, %mul_231), kwargs = {})
#   %convert_element_type_316 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_111, torch.bfloat16), kwargs = {})
#   %add_112 : [num_users=3] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_100, %convert_element_type_316), kwargs = {})
#   %mul_232 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_112, %select_1), kwargs = {})
#   %mul_233 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_112, %convert_element_type_1), kwargs = {})
#   %sum_30 : [num_users=1] = call_function[target=torch.ops.aten.sum.default](args = (%mul_233,), kwargs = {dtype: torch.float32})
#   %add_113 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_96, %mul_232), kwargs = {})
#   %mul_234 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_112, %select), kwargs = {})
#   %add_115 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_113, %mul_234), kwargs = {})
#   %convert_element_type_317 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_115, torch.float32), kwargs = {})
#   %mul_236 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_317, %convert_element_type), kwargs = {})
#   %mul_237 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_317, %rsqrt), kwargs = {})
#   %sum_32 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mul_236, [2], True), kwargs = {dtype: torch.float32})
#   %div_21 : [num_users=1] = call_function[target=torch.ops.aten.div.Scalar](args = (%expand_25, 256), kwargs = {})
#   %pow_62 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type, 1.0), kwargs = {})
#   %mul_240 : [num_users=1] = call_function[target=torch.ops.aten.mul.Scalar](args = (%pow_62, 2.0), kwargs = {})
#   %mul_241 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%div_21, %mul_240), kwargs = {})
#   %add_117 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_237, %mul_241), kwargs = {})
#   %where_10 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%unsqueeze_12, %full_default_1, %add_117), kwargs = {})
triton_per_fused__to_copy_add_div_embedding_dense_backward_mul_nll_loss_forward_pow_sum_21 = async_compile.triton('triton_per_fused__to_copy_add_div_embedding_dense_backward_mul_nll_loss_forward_pow_sum_21', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 32768, 'r': 256},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'in_ptr3': '*fp32', 'in_ptr4': '*bf16', 'in_ptr5': '*bf16', 'in_ptr6': '*bf16', 'in_ptr7': '*bf16', 'in_ptr8': '*fp32', 'in_ptr9': '*fp32', 'in_ptr10': '*fp32', 'in_ptr11': '*bf16', 'in_ptr12': '*bf16', 'in_ptr13': '*bf16', 'in_ptr14': '*i64', 'in_ptr15': '*bf16', 'in_ptr16': '*bf16', 'out_ptr0': '*fp32', 'out_ptr1': '*fp32', 'out_ptr4': '*fp32', 'out_ptr6': '*fp32', 'out_ptr7': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_div_embedding_dense_backward_mul_nll_loss_forward_pow_sum_21', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': True, 'num_load': 21, 'num_reduction': 5, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_div_embedding_dense_backward_mul_nll_loss_forward_pow_sum_21(in_out_ptr0, in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, in_ptr5, in_ptr6, in_ptr7, in_ptr8, in_ptr9, in_ptr10, in_ptr11, in_ptr12, in_ptr13, in_ptr14, in_ptr15, in_ptr16, out_ptr0, out_ptr1, out_ptr4, out_ptr6, out_ptr7, xnumel, rnumel):
    xnumel = 32768
    XBLOCK: tl.constexpr = 1
    rnumel = 256
    RBLOCK: tl.constexpr = 256
    xoffset = tl.program_id(0) * XBLOCK
    xindex = tl.full([1], xoffset, tl.int32)
    xmask = tl.full([RBLOCK], True, tl.int1)
    rindex = tl.arange(0, RBLOCK)[:]
    roffset = 0
    rmask = tl.full([RBLOCK], True, tl.int1)
    r1 = rindex
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (r1 + 256*x0), None).to(tl.float32)
    tmp1 = tl.load(in_ptr1 + (r1 + 256*x0), None).to(tl.float32)
    tmp3 = tl.load(in_ptr2 + (r1 + 256*x0), None).to(tl.float32)
    tmp5 = tl.load(in_ptr3 + (x0), None, eviction_policy='evict_last')
    tmp13 = tl.load(in_ptr4 + (r1 + 256*x0), None).to(tl.float32)
    tmp19 = tl.load(in_ptr5 + (r1 + 256*x0), None).to(tl.float32)
    tmp20 = tl.load(in_ptr6 + (r1 + 256*x0), None).to(tl.float32)
    tmp22 = tl.load(in_ptr7 + (r1 + 256*x0), None).to(tl.float32)
    tmp25 = tl.load(in_ptr8 + (0))
    tmp26 = tl.broadcast_to(tmp25, [RBLOCK])
    tmp29 = tl.load(in_ptr9 + (0))
    tmp30 = tl.broadcast_to(tmp29, [RBLOCK])
    tmp39 = tl.load(in_ptr10 + (x0), None, eviction_policy='evict_last')
    tmp52 = tl.load(in_out_ptr0 + (r1 + 256*x0), None).to(tl.float32)
    tmp53 = tl.load(in_ptr11 + (r1 + 256*x0), None).to(tl.float32)
    tmp55 = tl.load(in_ptr9 + (3))
    tmp56 = tl.broadcast_to(tmp55, [RBLOCK])
    tmp59 = tl.load(in_ptr12 + (r1 + 256*x0), None).to(tl.float32)
    tmp60 = tl.load(in_ptr9 + (2))
    tmp61 = tl.broadcast_to(tmp60, [RBLOCK])
    tmp65 = tl.load(in_ptr9 + (1))
    tmp66 = tl.broadcast_to(tmp65, [RBLOCK])
    tmp70 = tl.load(in_ptr13 + (r1 + 256*x0), None).to(tl.float32)
    tmp87 = tl.load(in_ptr14 + (x0), None, eviction_policy='evict_last')
    tmp90 = tl.load(in_ptr15 + (r1 + 256*x0), None).to(tl.float32)
    tmp91 = tl.load(in_ptr16 + (2*x0 + (r1 // 128)), None, eviction_policy='evict_last').to(tl.float32)
    tmp2 = tmp0 + tmp1
    tmp4 = tmp3.to(tl.float32)
    tmp6 = tmp4 * tmp5
    tmp7 = tmp6.to(tl.float32)
    tmp8 = tmp2 * tmp7
    tmp9 = tmp8.to(tl.float32)
    tmp10 = tl.broadcast_to(tmp9, [RBLOCK])
    tmp12 = triton_helpers.promote_to_tensor(tl.sum(tmp10, 0))
    tmp14 = tmp2 * tmp13
    tmp15 = tmp14.to(tl.float32)
    tmp16 = tl.broadcast_to(tmp15, [RBLOCK])
    tmp18 = triton_helpers.promote_to_tensor(tl.sum(tmp16, 0))
    tmp21 = tmp19 + tmp20
    tmp23 = tmp21 + tmp22
    tmp24 = tmp23.to(tl.float32)
    tmp27 = tmp26.to(tl.float32)
    tmp28 = tmp27 * tmp7
    tmp31 = tmp30.to(tl.float32)
    tmp32 = tmp31 * tmp7
    tmp33 = tmp28 + tmp32
    tmp34 = tmp33.to(tl.float32)
    tmp35 = tmp24 * tmp34
    tmp36 = tl.broadcast_to(tmp35, [RBLOCK])
    tmp38 = triton_helpers.promote_to_tensor(tl.sum(tmp36, 0))
    tmp40 = tmp24 * tmp39
    tmp41 = -0.5
    tmp42 = tmp38 * tmp41
    tmp43 = tmp39 * tmp39
    tmp44 = tmp43 * tmp39
    tmp45 = tmp42 * tmp44
    tmp46 = 0.00390625
    tmp47 = tmp45 * tmp46
    tmp48 = 2.0
    tmp49 = tmp34 * tmp48
    tmp50 = tmp47 * tmp49
    tmp51 = tmp40 + tmp50
    tmp54 = tmp52 + tmp53
    tmp57 = tmp56.to(tl.float32)
    tmp58 = tmp54 * tmp57
    tmp62 = tmp61.to(tl.float32)
    tmp63 = tmp59 * tmp62
    tmp64 = tmp58 + tmp63
    tmp67 = tmp66.to(tl.float32)
    tmp68 = tmp2 * tmp67
    tmp69 = tmp64 + tmp68
    tmp71 = tmp51.to(tl.float32)
    tmp72 = tmp70 + tmp71
    tmp73 = tmp72 * tmp31
    tmp74 = tmp69 + tmp73
    tmp75 = tmp72 * tmp7
    tmp76 = tmp75.to(tl.float32)
    tmp77 = tl.broadcast_to(tmp76, [RBLOCK])
    tmp79 = triton_helpers.promote_to_tensor(tl.sum(tmp77, 0))
    tmp80 = tmp72 * tmp27
    tmp81 = tmp74 + tmp80
    tmp82 = tmp81.to(tl.float32)
    tmp83 = tmp82 * tmp4
    tmp84 = tl.broadcast_to(tmp83, [RBLOCK])
    tmp86 = triton_helpers.promote_to_tensor(tl.sum(tmp84, 0))
    tmp88 = tl.full([1], -1, tl.int64)
    tmp89 = tmp87 == tmp88
    tmp92 = tl.sigmoid(tmp91)
    tmp93 = tmp92 * tmp48
    tmp94 = tmp90 * tmp93
    tmp95 = tmp94.to(tl.float32)
    tmp96 = 0.0
    tmp97 = tl.where(tmp89, tmp96, tmp95)
    tmp98 = tmp82 * tmp5
    tmp99 = tmp86 * tmp41
    tmp100 = tmp5 * tmp5
    tmp101 = tmp100 * tmp5
    tmp102 = tmp99 * tmp101
    tmp103 = tmp102 * tmp46
    tmp104 = tmp4 * tmp48
    tmp105 = tmp103 * tmp104
    tmp106 = tmp98 + tmp105
    tmp107 = tl.where(tmp89, tmp96, tmp106)
    tl.store(out_ptr6 + (r1 + 256*x0), tmp97, None)
    tl.store(out_ptr7 + (r1 + 256*x0), tmp107, None)
    tl.store(out_ptr0 + (x0), tmp12, None)
    tl.store(out_ptr1 + (x0), tmp18, None)
    tl.store(out_ptr4 + (x0), tmp79, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_smoke/s002/work/.ar_cache/inductor/fw/cfwods2geyfr2dpgumryec7vkuaxkea2zfs4s6uszipmqmpxje6s.py
# Topologically Sorted Source Nodes: [], Original ATen: [aten.select_backward, aten.add]
# Source node to ATen node mapping:
# Graph fragment:
#   %full_default_13 : [num_users=7] = call_function[target=torch.ops.aten.full.default](args = ([4], 0), kwargs = {dtype: torch.float32, layout: torch.strided, device: cuda:0, pin_memory: False})
#   %select_scatter_default : [num_users=1] = call_function[target=torch.ops.aten.select_scatter.default](args = (%full_default_13, %sum_11, 0, 3), kwargs = {})
#   %select_scatter_default_2 : [num_users=1] = call_function[target=torch.ops.aten.select_scatter.default](args = (%full_default_13, %sum_17, 0, 2), kwargs = {})
#   %add_79 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%select_scatter_default, %select_scatter_default_2), kwargs = {})
#   %select_scatter_default_4 : [num_users=1] = call_function[target=torch.ops.aten.select_scatter.default](args = (%full_default_13, %sum_24, 0, 1), kwargs = {})
#   %add_97 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_79, %select_scatter_default_4), kwargs = {})
#   %select_scatter_default_6 : [num_users=2] = call_function[target=torch.ops.aten.select_scatter.default](args = (%full_default_13, %sum_30, 0, 0), kwargs = {})
#   %add_114 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_97, %select_scatter_default_6), kwargs = {})
triton_poi_fused_add_select_backward_22 = async_compile.triton('triton_poi_fused_add_select_backward_22', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.pointwise(
    size_hints={'x': 4}, 
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*fp32', 'in_ptr1': '*fp32', 'in_ptr2': '*fp32', 'in_ptr3': '*fp32', 'out_ptr0': '*fp32', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_add_select_backward_22', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 4, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_add_select_backward_22(in_ptr0, in_ptr1, in_ptr2, in_ptr3, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 4
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
    tmp0 = x0
    tmp1 = tl.full([1], 3, tl.int32)
    tmp2 = tmp0 == tmp1
    tmp5 = 0.0
    tmp6 = tl.where(tmp2, tmp4, tmp5)
    tmp7 = tl.full([1], 2, tl.int32)
    tmp8 = tmp0 == tmp7
    tmp11 = tl.where(tmp8, tmp10, tmp5)
    tmp12 = tmp6 + tmp11
    tmp13 = tl.full([1], 1, tl.int32)
    tmp14 = tmp0 == tmp13
    tmp17 = tl.where(tmp14, tmp16, tmp5)
    tmp18 = tmp12 + tmp17
    tmp19 = tl.full([1], 0, tl.int32)
    tmp20 = tmp0 == tmp19
    tmp23 = tl.where(tmp20, tmp22, tmp5)
    tmp24 = tmp18 + tmp23
    tl.store(out_ptr0 + (x0), tmp24, xmask)
''', device_str='cuda')


async_compile.wait(globals())
del async_compile

def call(args):
    primals_1, primals_5, primals_6, primals_36, slice_2, slice_4, embedding, rsqrt, rsqrt_1, view, cat, cat_1, rsqrt_2, rsqrt_3, permute_3, permute_4, permute_5, getitem, getitem_1, getitem_6, getitem_7, add_9, rsqrt_4, view_14, mm_4, view_16, add_11, add_12, embedding_1, rsqrt_5, view_18, view_28, mm_9, cat_2, cat_3, rsqrt_6, rsqrt_7, permute_14, permute_15, permute_16, getitem_9, getitem_10, getitem_15, getitem_16, add_21, rsqrt_8, view_35, mm_11, view_37, add_23, add_24, rsqrt_9, view_39, cat_4, cat_5, rsqrt_10, rsqrt_11, permute_24, permute_25, permute_26, getitem_18, getitem_19, getitem_24, getitem_25, add_32, rsqrt_12, view_53, mm_17, view_55, add_34, add_35, embedding_2, rsqrt_13, view_57, view_67, mm_22, cat_6, cat_7, rsqrt_14, rsqrt_15, permute_35, permute_36, permute_37, getitem_27, getitem_28, getitem_33, getitem_34, add_44, rsqrt_16, view_74, mm_24, view_76, add_46, rsqrt_17, view_78, mm_26, amax, log, convert_element_type_126, permute_45, permute_49, permute_53, permute_57, permute_65, permute_69, permute_73, permute_77, permute_81, permute_85, permute_89, permute_97, permute_101, permute_105, permute_109, permute_113, permute_117, permute_125, permute_129, permute_133, permute_137, permute_141, permute_145, permute_149, permute_157, permute_161, permute_165, tangents_1 = args
    args.clear()
    assert_size_stride(primals_1, (16, 2048), (2048, 1))
    assert_size_stride(primals_5, (4, ), (1, ))
    assert_size_stride(primals_6, (4, ), (1, ))
    assert_size_stride(primals_36, (16, 2048), (2048, 1))
    assert_size_stride(slice_2, (1, 2048, 1, 64), (1310720, 64, 64, 1))
    assert_size_stride(slice_4, (1, 2048, 1, 64), (1310720, 64, 64, 1))
    assert_size_stride(embedding, (16, 2048, 256), (524288, 256, 1))
    assert_size_stride(rsqrt, (16, 2048, 1), (2048, 1, 1))
    assert_size_stride(rsqrt_1, (16, 2048, 1), (2048, 1, 1))
    assert_size_stride(view, (32768, 256), (256, 1))
    assert_size_stride(cat, (16, 2048, 2, 128), (524288, 256, 128, 1))
    assert_size_stride(cat_1, (16, 2048, 2, 128), (524288, 256, 128, 1))
    assert_size_stride(rsqrt_2, (16, 2048, 2, 1), (4096, 2, 1, 1))
    assert_size_stride(rsqrt_3, (16, 2048, 2, 1), (4096, 2, 1, 1))
    assert_size_stride(permute_3, (16, 2, 2048, 128), (524288, 128, 256, 1))
    assert_size_stride(permute_4, (16, 2, 2048, 128), (524288, 128, 256, 1))
    assert_size_stride(permute_5, (16, 2, 2048, 128), (524288, 128, 256, 1))
    assert_size_stride(getitem, (16, 2, 2048, 128), (524288, 128, 256, 1))
    assert_size_stride(getitem_1, (16, 2, 2048), (4096, 2048, 1))
    assert_size_stride(getitem_6, (), ())
    assert_size_stride(getitem_7, (), ())
    assert_size_stride(add_9, (16, 2048, 256), (524288, 256, 1))
    assert_size_stride(rsqrt_4, (16, 2048, 1), (2048, 1, 1))
    assert_size_stride(view_14, (32768, 256), (256, 1))
    assert_size_stride(mm_4, (32768, 1024), (1024, 1))
    assert_size_stride(view_16, (32768, 1024), (1024, 1))
    assert_size_stride(add_11, (16, 2048, 256), (524288, 256, 1))
    assert_size_stride(add_12, (16, 2048, 256), (524288, 256, 1))
    assert_size_stride(embedding_1, (16, 2048, 256), (524288, 256, 1))
    assert_size_stride(rsqrt_5, (16, 2048, 1), (2048, 1, 1))
    assert_size_stride(view_18, (32768, 256), (256, 1))
    assert_size_stride(view_28, (32768, 32), (256, 1))
    assert_size_stride(mm_9, (32768, 2), (2, 1))
    assert_size_stride(cat_2, (16, 2048, 2, 128), (524288, 256, 128, 1))
    assert_size_stride(cat_3, (16, 2048, 2, 128), (524288, 256, 128, 1))
    assert_size_stride(rsqrt_6, (16, 2048, 2, 1), (4096, 2, 1, 1))
    assert_size_stride(rsqrt_7, (16, 2048, 2, 1), (4096, 2, 1, 1))
    assert_size_stride(permute_14, (16, 2, 2048, 128), (524288, 128, 256, 1))
    assert_size_stride(permute_15, (16, 2, 2048, 128), (524288, 128, 256, 1))
    assert_size_stride(permute_16, (16, 2, 2048, 128), (524288, 128, 256, 1))
    assert_size_stride(getitem_9, (16, 2, 2048, 128), (524288, 128, 256, 1))
    assert_size_stride(getitem_10, (16, 2, 2048), (4096, 2048, 1))
    assert_size_stride(getitem_15, (), ())
    assert_size_stride(getitem_16, (), ())
    assert_size_stride(add_21, (16, 2048, 256), (524288, 256, 1))
    assert_size_stride(rsqrt_8, (16, 2048, 1), (2048, 1, 1))
    assert_size_stride(view_35, (32768, 256), (256, 1))
    assert_size_stride(mm_11, (32768, 1024), (1024, 1))
    assert_size_stride(view_37, (32768, 1024), (1024, 1))
    assert_size_stride(add_23, (16, 2048, 256), (524288, 256, 1))
    assert_size_stride(add_24, (16, 2048, 256), (524288, 256, 1))
    assert_size_stride(rsqrt_9, (16, 2048, 1), (2048, 1, 1))
    assert_size_stride(view_39, (32768, 256), (256, 1))
    assert_size_stride(cat_4, (16, 2048, 2, 128), (524288, 256, 128, 1))
    assert_size_stride(cat_5, (16, 2048, 2, 128), (524288, 256, 128, 1))
    assert_size_stride(rsqrt_10, (16, 2048, 2, 1), (4096, 2, 1, 1))
    assert_size_stride(rsqrt_11, (16, 2048, 2, 1), (4096, 2, 1, 1))
    assert_size_stride(permute_24, (16, 2, 2048, 128), (524288, 128, 256, 1))
    assert_size_stride(permute_25, (16, 2, 2048, 128), (524288, 128, 256, 1))
    assert_size_stride(permute_26, (16, 2, 2048, 128), (524288, 128, 256, 1))
    assert_size_stride(getitem_18, (16, 2, 2048, 128), (524288, 128, 256, 1))
    assert_size_stride(getitem_19, (16, 2, 2048), (4096, 2048, 1))
    assert_size_stride(getitem_24, (), ())
    assert_size_stride(getitem_25, (), ())
    assert_size_stride(add_32, (16, 2048, 256), (524288, 256, 1))
    assert_size_stride(rsqrt_12, (16, 2048, 1), (2048, 1, 1))
    assert_size_stride(view_53, (32768, 256), (256, 1))
    assert_size_stride(mm_17, (32768, 1024), (1024, 1))
    assert_size_stride(view_55, (32768, 1024), (1024, 1))
    assert_size_stride(add_34, (16, 2048, 256), (524288, 256, 1))
    assert_size_stride(add_35, (16, 2048, 256), (524288, 256, 1))
    assert_size_stride(embedding_2, (16, 2048, 256), (524288, 256, 1))
    assert_size_stride(rsqrt_13, (16, 2048, 1), (2048, 1, 1))
    assert_size_stride(view_57, (32768, 256), (256, 1))
    assert_size_stride(view_67, (32768, 32), (256, 1))
    assert_size_stride(mm_22, (32768, 2), (2, 1))
    assert_size_stride(cat_6, (16, 2048, 2, 128), (524288, 256, 128, 1))
    assert_size_stride(cat_7, (16, 2048, 2, 128), (524288, 256, 128, 1))
    assert_size_stride(rsqrt_14, (16, 2048, 2, 1), (4096, 2, 1, 1))
    assert_size_stride(rsqrt_15, (16, 2048, 2, 1), (4096, 2, 1, 1))
    assert_size_stride(permute_35, (16, 2, 2048, 128), (524288, 128, 256, 1))
    assert_size_stride(permute_36, (16, 2, 2048, 128), (524288, 128, 256, 1))
    assert_size_stride(permute_37, (16, 2, 2048, 128), (524288, 128, 256, 1))
    assert_size_stride(getitem_27, (16, 2, 2048, 128), (524288, 128, 256, 1))
    assert_size_stride(getitem_28, (16, 2, 2048), (4096, 2048, 1))
    assert_size_stride(getitem_33, (), ())
    assert_size_stride(getitem_34, (), ())
    assert_size_stride(add_44, (16, 2048, 256), (524288, 256, 1))
    assert_size_stride(rsqrt_16, (16, 2048, 1), (2048, 1, 1))
    assert_size_stride(view_74, (32768, 256), (256, 1))
    assert_size_stride(mm_24, (32768, 1024), (1024, 1))
    assert_size_stride(view_76, (32768, 1024), (1024, 1))
    assert_size_stride(add_46, (16, 2048, 256), (524288, 256, 1))
    assert_size_stride(rsqrt_17, (16, 2048, 1), (2048, 1, 1))
    assert_size_stride(view_78, (32768, 256), (256, 1))
    assert_size_stride(mm_26, (32768, 8192), (8192, 1))
    assert_size_stride(amax, (32768, 1), (1, 1))
    assert_size_stride(log, (32768, 1), (1, 1))
    assert_size_stride(convert_element_type_126, (), ())
    assert_size_stride(permute_45, (8192, 256), (256, 1))
    assert_size_stride(permute_49, (256, 1024), (1024, 1))
    assert_size_stride(permute_53, (1024, 256), (256, 1))
    assert_size_stride(permute_57, (256, 256), (256, 1))
    assert_size_stride(permute_65, (2, 32), (32, 1))
    assert_size_stride(permute_69, (256, 256), (256, 1))
    assert_size_stride(permute_73, (256, 256), (256, 1))
    assert_size_stride(permute_77, (256, 256), (256, 1))
    assert_size_stride(permute_81, (256, 1024), (1024, 1))
    assert_size_stride(permute_85, (1024, 256), (256, 1))
    assert_size_stride(permute_89, (256, 256), (256, 1))
    assert_size_stride(permute_97, (256, 256), (256, 1))
    assert_size_stride(permute_101, (256, 256), (256, 1))
    assert_size_stride(permute_105, (256, 256), (256, 1))
    assert_size_stride(permute_109, (256, 1024), (1024, 1))
    assert_size_stride(permute_113, (1024, 256), (256, 1))
    assert_size_stride(permute_117, (256, 256), (256, 1))
    assert_size_stride(permute_125, (2, 32), (32, 1))
    assert_size_stride(permute_129, (256, 256), (256, 1))
    assert_size_stride(permute_133, (256, 256), (256, 1))
    assert_size_stride(permute_137, (256, 256), (256, 1))
    assert_size_stride(permute_141, (256, 1024), (1024, 1))
    assert_size_stride(permute_145, (1024, 256), (256, 1))
    assert_size_stride(permute_149, (256, 256), (256, 1))
    assert_size_stride(permute_157, (256, 256), (256, 1))
    assert_size_stride(permute_161, (256, 256), (256, 1))
    assert_size_stride(permute_165, (256, 256), (256, 1))
    assert_size_stride(tangents_1, (), ())
    with torch.cuda._DeviceGuard(0):
        torch.cuda.set_device(0)
        buf2 = reinterpret_tensor(mm_26, (16, 2048, 8192), (16777216, 8192, 1), 0); del mm_26  # reuse
        # Topologically Sorted Source Nodes: [loss, logits_1, truediv, tanh], Original ATen: [aten.nll_loss_backward, aten.nll_loss_forward, aten._to_copy, aten.div, aten.tanh, aten._log_softmax, aten._log_softmax_backward_data, aten.mul, aten.tanh_backward]
        stream0 = get_raw_stream(0)
        triton_red_fused__log_softmax__log_softmax_backward_data__to_copy_div_mul_nll_loss_backward_nll_loss_forward_tanh_tanh_backward_0.run(buf2, primals_36, tangents_1, convert_element_type_126, amax, log, 32768, 8192, grid=grid(32768), stream=stream0)
        del amax
        del convert_element_type_126
        del log
        del primals_36
        del tangents_1
        buf3 = empty_strided_cuda((8192, 256), (256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf2, (8192, 32768), (1, 8192), 0), view_78, out=buf3)
        del view_78
        buf4 = empty_strided_cuda((32768, 256), (256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf2, (32768, 8192), (8192, 1), 0), permute_45, out=buf4)
        del buf2
        del permute_45
        buf5 = empty_strided_cuda((8192, 256), (256, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_1.run(buf3, buf5, 2097152, grid=grid(2097152), stream=stream0)
        buf7 = reinterpret_tensor(buf4, (16, 2048, 256), (524288, 256, 1), 0); del buf4  # reuse
        # Topologically Sorted Source Nodes: [x_26], Original ATen: [aten._to_copy, aten.mul, aten.sum, aten.div, aten.pow, aten.add]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_div_mul_pow_sum_2.run(buf7, add_46, rsqrt_17, 32768, 256, grid=grid(32768), stream=stream0)
        del add_46
        del rsqrt_17
        buf8 = empty_strided_cuda((256, 1024), (1024, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf7, (256, 32768), (1, 256), 0), view_76, out=buf8)
        del view_76
        buf9 = empty_strided_cuda((32768, 1024), (1024, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf7, (32768, 256), (256, 1), 0), permute_49, out=buf9)
        del permute_49
        buf10 = empty_strided_cuda((256, 1024), (1024, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_3.run(buf8, buf10, 262144, grid=grid(262144), stream=stream0)
        buf11 = reinterpret_tensor(mm_24, (16, 2048, 1024), (2097152, 1024, 1), 0); del mm_24  # reuse
        # Topologically Sorted Source Nodes: [relu_3, x_23], Original ATen: [aten._to_copy, aten.relu, aten.pow, aten.mul, aten.threshold_backward]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_mul_pow_relu_threshold_backward_4.run(buf11, buf9, 33554432, grid=grid(33554432), stream=stream0)
        del buf9
        buf12 = reinterpret_tensor(buf8, (1024, 256), (256, 1), 0); del buf8  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf11, (1024, 32768), (1, 1024), 0), view_74, out=buf12)
        del view_74
        buf13 = empty_strided_cuda((32768, 256), (256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf11, (32768, 1024), (1024, 1), 0), permute_53, out=buf13)
        del permute_53
        buf14 = empty_strided_cuda((1024, 256), (256, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_3.run(buf12, buf14, 262144, grid=grid(262144), stream=stream0)
        buf16 = buf7; del buf7  # reuse
        # Topologically Sorted Source Nodes: [rms_norm_16], Original ATen: [aten._to_copy, aten.mul, aten.sum, aten.div, aten.pow, aten.add]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_div_mul_pow_sum_5.run(buf16, buf13, add_44, rsqrt_16, 32768, 256, grid=grid(32768), stream=stream0)
        del add_44
        del rsqrt_16
        buf17 = empty_strided_cuda((256, 256), (256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf16, (256, 32768), (1, 256), 0), reinterpret_tensor(getitem_27, (32768, 256), (256, 1), 0), out=buf17)
        buf18 = buf13; del buf13  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf16, (32768, 256), (256, 1), 0), permute_57, out=buf18)
        del permute_57
        buf19 = empty_strided_cuda((256, 256), (256, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf17, buf19, 65536, grid=grid(65536), stream=stream0)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._scaled_dot_product_flash_attention_backward]
        buf20 = torch.ops.aten._scaled_dot_product_flash_attention_backward.default(reinterpret_tensor(buf18, (16, 2, 2048, 128), (524288, 128, 256, 1), 0), permute_35, permute_36, permute_37, getitem_27, getitem_28, None, None, 2048, 2048, 0.0, True, getitem_33, getitem_34, scale=0.08838834764831843)
        del getitem_27
        del getitem_28
        del getitem_33
        del getitem_34
        del permute_35
        del permute_36
        del permute_37
        buf21 = buf20[0]
        buf22 = buf20[1]
        buf23 = buf20[2]
        del buf20
        buf24 = empty_strided_cuda((16, 2048, 2, 1), (4096, 2, 1, 65536), torch.float32)
        # Topologically Sorted Source Nodes: [k_17], Original ATen: [aten._to_copy, aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_mul_sum_7.run(buf22, cat_7, buf24, 65536, 128, grid=grid(65536), stream=stream0)
        buf25 = empty_strided_cuda((16, 2048, 2, 1), (4096, 2, 1, 65536), torch.float32)
        # Topologically Sorted Source Nodes: [q_14], Original ATen: [aten._to_copy, aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_mul_sum_7.run(buf21, cat_6, buf25, 65536, 128, grid=grid(65536), stream=stream0)
        buf26 = empty_strided_cuda((16, 2048, 2, 64), (262144, 128, 64, 1), torch.bfloat16)
        buf27 = empty_strided_cuda((16, 2048, 2, 64), (262144, 128, 64, 1), torch.bfloat16)
        buf28 = empty_strided_cuda((16, 2048, 2, 64), (262144, 128, 64, 1), torch.bfloat16)
        buf29 = empty_strided_cuda((16, 2048, 2, 64), (262144, 128, 64, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [neg], Original ATen: [aten.mul, aten.neg, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_mul_neg_8.run(buf22, rsqrt_15, buf24, cat_7, slice_2, slice_4, buf21, rsqrt_14, buf25, cat_6, buf26, buf27, buf28, buf29, 4194304, grid=grid(4194304), stream=stream0)
        del cat_6
        del cat_7
        del rsqrt_14
        del rsqrt_15
        buf49 = empty_strided_cuda((16, 2048, 256), (524288, 256, 1), torch.float32)
        buf31 = reinterpret_tensor(buf17, (16, 2048, 2), (4096, 2, 1), 0); del buf17  # reuse
        # Topologically Sorted Source Nodes: [loss, sigmoid_1], Original ATen: [aten.nll_loss_forward, aten.sigmoid, aten.mul, aten.sum, aten.sigmoid_backward, aten.embedding_dense_backward]
        stream0 = get_raw_stream(0)
        triton_per_fused_embedding_dense_backward_mul_nll_loss_forward_sigmoid_sigmoid_backward_sum_9.run(buf23, embedding_2, primals_1, mm_22, buf49, buf31, 65536, 128, grid=grid(65536), stream=stream0)
        del embedding_2
        del mm_22
        buf32 = empty_strided_cuda((2, 32), (32, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf31, (2, 32768), (1, 2), 0), view_67, out=buf32)
        del view_67
        buf33 = empty_strided_cuda((32768, 32), (32, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf31, (32768, 2), (2, 1), 0), permute_65, out=buf33)
        del permute_65
        buf34 = empty_strided_cuda((2, 32), (32, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_10.run(buf32, buf34, 64, grid=grid(64), stream=stream0)
        buf35 = reinterpret_tensor(buf31, (256, 256), (256, 1), 0); del buf31  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf23, (256, 32768), (1, 256), 0), view_57, out=buf35)
        buf36 = reinterpret_tensor(buf22, (32768, 256), (256, 1), 0); del buf22  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf23, (32768, 256), (256, 1), 0), permute_69, out=buf36)
        del permute_69
        buf37 = reinterpret_tensor(buf25, (256, 256), (256, 1), 0); del buf25  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf35, buf37, 65536, grid=grid(65536), stream=stream0)
        buf38 = reinterpret_tensor(buf23, (16, 2048, 2, 128), (524288, 256, 128, 1), 0); del buf23  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.slice_backward, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_slice_backward_11.run(buf26, buf27, buf38, 8388608, grid=grid(8388608), stream=stream0)
        buf39 = buf35; del buf35  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf38, (256, 32768), (1, 256), 0), view_57, out=buf39)
        buf40 = reinterpret_tensor(buf21, (32768, 256), (256, 1), 0); del buf21  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf38, (32768, 256), (256, 1), 0), permute_73, out=buf40)
        del permute_73
        buf41 = reinterpret_tensor(buf24, (256, 256), (256, 1), 0); del buf24  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf39, buf41, 65536, grid=grid(65536), stream=stream0)
        buf42 = buf38; del buf38  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.slice_backward, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_slice_backward_11.run(buf28, buf29, buf42, 8388608, grid=grid(8388608), stream=stream0)
        buf43 = buf39; del buf39  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf42, (256, 32768), (1, 256), 0), view_57, out=buf43)
        del view_57
        buf44 = buf18; del buf18  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf42, (32768, 256), (256, 1), 0), permute_77, out=buf44)
        del permute_77
        buf45 = empty_strided_cuda((256, 256), (256, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf43, buf45, 65536, grid=grid(65536), stream=stream0)
        buf47 = reinterpret_tensor(buf36, (16, 2048, 256), (524288, 256, 1), 0); del buf36  # reuse
        buf56 = reinterpret_tensor(buf42, (16, 2048, 256), (524288, 256, 1), 0); del buf42  # reuse
        # Topologically Sorted Source Nodes: [rms_norm_13], Original ATen: [aten.slice_backward, aten.add, aten._to_copy, aten.mul, aten.sum, aten.div, aten.pow]
        stream0 = get_raw_stream(0)
        triton_red_fused__to_copy_add_div_mul_pow_slice_backward_sum_12.run(buf47, buf33, buf40, buf44, add_35, rsqrt_13, buf16, primals_5, buf56, 32768, 256, grid=grid(32768), stream=stream0)
        del add_35
        del rsqrt_13
        buf48 = empty_strided_cuda((8192, 256), (256, 1), torch.float32)
        # Topologically Sorted Source Nodes: [loss], Original ATen: [aten.nll_loss_forward, aten.embedding_dense_backward]
        stream0 = get_raw_stream(0)
        triton_poi_fused_embedding_dense_backward_nll_loss_forward_13.run(buf48, 2097152, grid=grid(2097152), stream=stream0)
        aten.index_put_(buf48, [primals_1], buf49, True)
        buf51 = buf3; del buf3  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.embedding_dense_backward]
        stream0 = get_raw_stream(0)
        triton_poi_fused_embedding_dense_backward_14.run(buf48, buf51, 2097152, grid=grid(2097152), stream=stream0)
        buf58 = reinterpret_tensor(buf11, (32768, 1024), (1024, 1), 0); del buf11  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf56, (32768, 256), (256, 1), 0), permute_81, out=buf58)
        del permute_81
        buf60 = reinterpret_tensor(mm_17, (16, 2048, 1024), (2097152, 1024, 1), 0); del mm_17  # reuse
        # Topologically Sorted Source Nodes: [relu_2, x_17], Original ATen: [aten.threshold_backward, aten._to_copy, aten.relu, aten.pow, aten.mul]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_mul_pow_relu_threshold_backward_4.run(buf60, buf58, 33554432, grid=grid(33554432), stream=stream0)
        del buf58
        buf62 = buf44; del buf44  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf60, (32768, 1024), (1024, 1), 0), permute_85, out=buf62)
        del permute_85
        buf65 = reinterpret_tensor(buf62, (16, 2048, 256), (524288, 256, 1), 0); del buf62  # reuse
        # Topologically Sorted Source Nodes: [rms_norm_12], Original ATen: [aten._to_copy, aten.mul, aten.sum, aten.div, aten.pow, aten.add]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_div_mul_pow_sum_15.run(buf65, add_32, buf56, rsqrt_12, 32768, 256, grid=grid(32768), stream=stream0)
        del add_32
        del rsqrt_12
        buf67 = buf40; del buf40  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf65, (32768, 256), (256, 1), 0), permute_89, out=buf67)
        del permute_89
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._scaled_dot_product_flash_attention_backward]
        buf69 = torch.ops.aten._scaled_dot_product_flash_attention_backward.default(reinterpret_tensor(buf67, (16, 2, 2048, 128), (524288, 128, 256, 1), 0), permute_24, permute_25, permute_26, getitem_18, getitem_19, None, None, 2048, 2048, 0.0, True, getitem_24, getitem_25, scale=0.08838834764831843)
        del getitem_19
        del getitem_24
        del getitem_25
        del permute_24
        del permute_25
        del permute_26
        buf72 = buf69[2]
        buf80 = buf67; del buf67  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf72, (32768, 256), (256, 1), 0), permute_97, out=buf80)
        del permute_97
        buf70 = buf69[0]
        buf71 = buf69[1]
        del buf69
        buf73 = empty_strided_cuda((16, 2048, 2, 1), (4096, 2, 1, 65536), torch.float32)
        # Topologically Sorted Source Nodes: [k_12], Original ATen: [aten._to_copy, aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_mul_sum_7.run(buf71, cat_5, buf73, 65536, 128, grid=grid(65536), stream=stream0)
        buf74 = empty_strided_cuda((16, 2048, 2, 1), (4096, 2, 1, 65536), torch.float32)
        # Topologically Sorted Source Nodes: [q_10], Original ATen: [aten._to_copy, aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_mul_sum_7.run(buf70, cat_4, buf74, 65536, 128, grid=grid(65536), stream=stream0)
        buf75 = buf29; del buf29  # reuse
        buf76 = buf28; del buf28  # reuse
        buf77 = buf27; del buf27  # reuse
        buf78 = buf26; del buf26  # reuse
        # Topologically Sorted Source Nodes: [neg], Original ATen: [aten.neg, aten.mul, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_mul_neg_8.run(buf71, rsqrt_11, buf73, cat_5, slice_2, slice_4, buf70, rsqrt_10, buf74, cat_4, buf75, buf76, buf77, buf78, 4194304, grid=grid(4194304), stream=stream0)
        del cat_4
        del cat_5
        del rsqrt_10
        del rsqrt_11
        buf82 = reinterpret_tensor(buf71, (16, 2048, 2, 128), (524288, 256, 128, 1), 0); del buf71  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.slice_backward, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_slice_backward_11.run(buf75, buf76, buf82, 8388608, grid=grid(8388608), stream=stream0)
        buf84 = reinterpret_tensor(buf70, (32768, 256), (256, 1), 0); del buf70  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf82, (32768, 256), (256, 1), 0), permute_101, out=buf84)
        del permute_101
        buf86 = empty_strided_cuda((16, 2048, 2, 128), (524288, 256, 128, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.slice_backward, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_slice_backward_11.run(buf77, buf78, buf86, 8388608, grid=grid(8388608), stream=stream0)
        buf88 = empty_strided_cuda((32768, 256), (256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf86, (32768, 256), (256, 1), 0), permute_105, out=buf88)
        del permute_105
        buf91 = reinterpret_tensor(buf80, (16, 2048, 256), (524288, 256, 1), 0); del buf80  # reuse
        buf96 = empty_strided_cuda((32768, 256), (256, 1), torch.bfloat16)
        buf52 = empty_strided_cuda((16, 2048, 1), (2048, 1, 32768), torch.float32)
        buf54 = empty_strided_cuda((16, 2048, 1), (2048, 1, 32768), torch.float32)
        buf92 = empty_strided_cuda((16, 2048, 1), (2048, 1, 32768), torch.float32)
        buf94 = empty_strided_cuda((16, 2048, 1), (2048, 1, 32768), torch.float32)
        # Topologically Sorted Source Nodes: [x_1, rms_norm_9], Original ATen: [aten.add, aten._to_copy, aten.mul, aten.sum, aten.div, aten.pow, aten.view]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_div_mul_pow_sum_view_16.run(buf91, buf84, buf88, add_24, buf65, rsqrt_9, primals_5, buf16, buf47, embedding, rsqrt, add_34, add_23, buf96, buf52, buf54, buf92, buf94, 32768, 256, grid=grid(32768), stream=stream0)
        del add_23
        del add_24
        del add_34
        del buf84
        del buf88
        del rsqrt_9
        buf53 = empty_strided_cuda((), (), torch.float32)
        # Topologically Sorted Source Nodes: [x_1], Original ATen: [aten.add, aten._to_copy, aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_red_fused__to_copy_add_mul_sum_17.run(buf52, buf53, 1, 32768, grid=grid(1), stream=stream0)
        del buf52
        buf55 = empty_strided_cuda((), (), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.add, aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_red_fused__to_copy_add_mul_sum_17.run(buf54, buf55, 1, 32768, grid=grid(1), stream=stream0)
        buf57 = reinterpret_tensor(buf12, (256, 1024), (1024, 1), 0); del buf12  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf56, (256, 32768), (1, 256), 0), view_55, out=buf57)
        del buf56
        del view_55
        buf59 = empty_strided_cuda((256, 1024), (1024, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_3.run(buf57, buf59, 262144, grid=grid(262144), stream=stream0)
        buf61 = reinterpret_tensor(buf57, (1024, 256), (256, 1), 0); del buf57  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf60, (1024, 32768), (1, 1024), 0), view_53, out=buf61)
        del view_53
        buf63 = empty_strided_cuda((1024, 256), (256, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_3.run(buf61, buf63, 262144, grid=grid(262144), stream=stream0)
        buf66 = buf43; del buf43  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf65, (256, 32768), (1, 256), 0), reinterpret_tensor(getitem_18, (32768, 256), (256, 1), 0), out=buf66)
        del getitem_18
        buf68 = reinterpret_tensor(buf74, (256, 256), (256, 1), 0); del buf74  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf66, buf68, 65536, grid=grid(65536), stream=stream0)
        buf79 = buf66; del buf66  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf72, (256, 32768), (1, 256), 0), view_39, out=buf79)
        buf81 = reinterpret_tensor(buf73, (256, 256), (256, 1), 0); del buf73  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf79, buf81, 65536, grid=grid(65536), stream=stream0)
        buf83 = buf79; del buf79  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf82, (256, 32768), (1, 256), 0), view_39, out=buf83)
        buf85 = empty_strided_cuda((256, 256), (256, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf83, buf85, 65536, grid=grid(65536), stream=stream0)
        buf87 = buf83; del buf83  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf86, (256, 32768), (1, 256), 0), view_39, out=buf87)
        del view_39
        buf89 = empty_strided_cuda((256, 256), (256, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf87, buf89, 65536, grid=grid(65536), stream=stream0)
        buf93 = empty_strided_cuda((), (), torch.float32)
        # Topologically Sorted Source Nodes: [x_1], Original ATen: [aten._to_copy, aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_red_fused__to_copy_add_mul_sum_17.run(buf92, buf93, 1, 32768, grid=grid(1), stream=stream0)
        buf95 = empty_strided_cuda((), (), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_red_fused__to_copy_add_mul_sum_17.run(buf94, buf95, 1, 32768, grid=grid(1), stream=stream0)
        buf97 = reinterpret_tensor(buf61, (256, 1024), (1024, 1), 0); del buf61  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf96, (256, 32768), (1, 256), 0), view_37, out=buf97)
        del view_37
        buf98 = reinterpret_tensor(buf60, (32768, 1024), (1024, 1), 0); del buf60  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(buf96, permute_109, out=buf98)
        del permute_109
        buf99 = empty_strided_cuda((256, 1024), (1024, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_3.run(buf97, buf99, 262144, grid=grid(262144), stream=stream0)
        buf100 = reinterpret_tensor(mm_11, (16, 2048, 1024), (2097152, 1024, 1), 0); del mm_11  # reuse
        # Topologically Sorted Source Nodes: [relu_1, x_11], Original ATen: [aten.threshold_backward, aten._to_copy, aten.relu, aten.pow, aten.mul]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_mul_pow_relu_threshold_backward_4.run(buf100, buf98, 33554432, grid=grid(33554432), stream=stream0)
        del buf98
        buf101 = reinterpret_tensor(buf97, (1024, 256), (256, 1), 0); del buf97  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf100, (1024, 32768), (1, 1024), 0), view_35, out=buf101)
        del view_35
        buf102 = buf96; del buf96  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf100, (32768, 1024), (1024, 1), 0), permute_113, out=buf102)
        del permute_113
        buf103 = empty_strided_cuda((1024, 256), (256, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_3.run(buf101, buf103, 262144, grid=grid(262144), stream=stream0)
        buf105 = reinterpret_tensor(buf102, (16, 2048, 256), (524288, 256, 1), 0); del buf102  # reuse
        # Topologically Sorted Source Nodes: [rms_norm_8], Original ATen: [aten.mul, aten._to_copy, aten.sum, aten.div, aten.pow, aten.add]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_div_mul_pow_sum_18.run(buf105, add_21, buf91, primals_5, rsqrt_8, 32768, 256, grid=grid(32768), stream=stream0)
        del add_21
        del rsqrt_8
        buf106 = buf87; del buf87  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf105, (256, 32768), (1, 256), 0), reinterpret_tensor(getitem_9, (32768, 256), (256, 1), 0), out=buf106)
        buf107 = reinterpret_tensor(buf86, (32768, 256), (256, 1), 0); del buf86  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf105, (32768, 256), (256, 1), 0), permute_117, out=buf107)
        del permute_117
        buf108 = empty_strided_cuda((256, 256), (256, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf106, buf108, 65536, grid=grid(65536), stream=stream0)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._scaled_dot_product_flash_attention_backward]
        buf109 = torch.ops.aten._scaled_dot_product_flash_attention_backward.default(reinterpret_tensor(buf107, (16, 2, 2048, 128), (524288, 128, 256, 1), 0), permute_14, permute_15, permute_16, getitem_9, getitem_10, None, None, 2048, 2048, 0.0, True, getitem_15, getitem_16, scale=0.08838834764831843)
        del getitem_10
        del getitem_15
        del getitem_16
        del getitem_9
        del permute_14
        del permute_15
        del permute_16
        buf110 = buf109[0]
        buf111 = buf109[1]
        buf112 = buf109[2]
        del buf109
        buf113 = empty_strided_cuda((16, 2048, 2, 1), (4096, 2, 1, 65536), torch.float32)
        # Topologically Sorted Source Nodes: [k_7], Original ATen: [aten._to_copy, aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_mul_sum_7.run(buf111, cat_3, buf113, 65536, 128, grid=grid(65536), stream=stream0)
        buf114 = empty_strided_cuda((16, 2048, 2, 1), (4096, 2, 1, 65536), torch.float32)
        # Topologically Sorted Source Nodes: [q_6], Original ATen: [aten._to_copy, aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_mul_sum_7.run(buf110, cat_2, buf114, 65536, 128, grid=grid(65536), stream=stream0)
        buf115 = buf78; del buf78  # reuse
        buf116 = buf77; del buf77  # reuse
        buf117 = buf76; del buf76  # reuse
        buf118 = buf75; del buf75  # reuse
        # Topologically Sorted Source Nodes: [neg], Original ATen: [aten.neg, aten.mul, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_mul_neg_8.run(buf111, rsqrt_7, buf113, cat_3, slice_2, slice_4, buf110, rsqrt_6, buf114, cat_2, buf115, buf116, buf117, buf118, 4194304, grid=grid(4194304), stream=stream0)
        del cat_2
        del cat_3
        del rsqrt_6
        del rsqrt_7
        buf120 = reinterpret_tensor(buf106, (16, 2048, 2), (4096, 2, 1), 0); del buf106  # reuse
        # Topologically Sorted Source Nodes: [sigmoid], Original ATen: [aten.sigmoid, aten.mul, aten.sum, aten.sigmoid_backward]
        stream0 = get_raw_stream(0)
        triton_per_fused_mul_sigmoid_sigmoid_backward_sum_19.run(buf112, embedding_1, mm_9, buf120, 65536, 128, grid=grid(65536), stream=stream0)
        del embedding_1
        buf121 = buf32; del buf32  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf120, (2, 32768), (1, 2), 0), view_28, out=buf121)
        del view_28
        buf122 = buf33; del buf33  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf120, (32768, 2), (2, 1), 0), permute_125, out=buf122)
        del permute_125
        buf123 = empty_strided_cuda((2, 32), (32, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_10.run(buf121, buf123, 64, grid=grid(64), stream=stream0)
        del buf121
        buf124 = reinterpret_tensor(buf120, (256, 256), (256, 1), 0); del buf120  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf112, (256, 32768), (1, 256), 0), view_18, out=buf124)
        buf125 = reinterpret_tensor(buf111, (32768, 256), (256, 1), 0); del buf111  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf112, (32768, 256), (256, 1), 0), permute_129, out=buf125)
        del permute_129
        buf126 = reinterpret_tensor(buf114, (256, 256), (256, 1), 0); del buf114  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf124, buf126, 65536, grid=grid(65536), stream=stream0)
        buf127 = reinterpret_tensor(buf110, (16, 2048, 2, 128), (524288, 256, 128, 1), 0); del buf110  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.slice_backward, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_slice_backward_11.run(buf115, buf116, buf127, 8388608, grid=grid(8388608), stream=stream0)
        buf128 = buf124; del buf124  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf127, (256, 32768), (1, 256), 0), view_18, out=buf128)
        buf129 = buf107; del buf107  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf127, (32768, 256), (256, 1), 0), permute_133, out=buf129)
        del permute_133
        buf130 = reinterpret_tensor(buf113, (256, 256), (256, 1), 0); del buf113  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf128, buf130, 65536, grid=grid(65536), stream=stream0)
        buf131 = buf127; del buf127  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.slice_backward, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_slice_backward_11.run(buf117, buf118, buf131, 8388608, grid=grid(8388608), stream=stream0)
        buf132 = buf128; del buf128  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf131, (256, 32768), (1, 256), 0), view_18, out=buf132)
        del view_18
        buf133 = reinterpret_tensor(buf82, (32768, 256), (256, 1), 0); del buf82  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf131, (32768, 256), (256, 1), 0), permute_137, out=buf133)
        del permute_137
        buf134 = empty_strided_cuda((256, 256), (256, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf132, buf134, 65536, grid=grid(65536), stream=stream0)
        buf136 = reinterpret_tensor(buf125, (16, 2048, 256), (524288, 256, 1), 0); del buf125  # reuse
        buf145 = reinterpret_tensor(buf131, (16, 2048, 256), (524288, 256, 1), 0); del buf131  # reuse
        # Topologically Sorted Source Nodes: [rms_norm_5], Original ATen: [aten.slice_backward, aten.add, aten._to_copy, aten.mul, aten.sum, aten.div, aten.pow]
        stream0 = get_raw_stream(0)
        triton_red_fused__to_copy_add_div_mul_pow_slice_backward_sum_20.run(buf136, buf122, buf129, buf133, add_12, rsqrt_5, buf105, primals_5, buf145, 32768, 256, grid=grid(32768), stream=stream0)
        del add_12
        del buf122
        del rsqrt_5
        buf137 = buf48; del buf48  # reuse
        # Topologically Sorted Source Nodes: [loss], Original ATen: [aten.nll_loss_forward, aten.embedding_dense_backward]
        stream0 = get_raw_stream(0)
        triton_poi_fused_embedding_dense_backward_nll_loss_forward_13.run(buf137, 2097152, grid=grid(2097152), stream=stream0)
        buf147 = reinterpret_tensor(buf100, (32768, 1024), (1024, 1), 0); del buf100  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf145, (32768, 256), (256, 1), 0), permute_141, out=buf147)
        del permute_141
        buf149 = reinterpret_tensor(mm_4, (16, 2048, 1024), (2097152, 1024, 1), 0); del mm_4  # reuse
        # Topologically Sorted Source Nodes: [relu, x_5], Original ATen: [aten.threshold_backward, aten._to_copy, aten.relu, aten.pow, aten.mul]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_mul_pow_relu_threshold_backward_4.run(buf149, buf147, 33554432, grid=grid(33554432), stream=stream0)
        del buf147
        buf151 = buf133; del buf133  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf149, (32768, 1024), (1024, 1), 0), permute_145, out=buf151)
        del permute_145
        buf154 = reinterpret_tensor(buf151, (16, 2048, 256), (524288, 256, 1), 0); del buf151  # reuse
        # Topologically Sorted Source Nodes: [rms_norm_4], Original ATen: [aten._to_copy, aten.mul, aten.sum, aten.div, aten.pow, aten.add]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_div_mul_pow_sum_15.run(buf154, add_9, buf145, rsqrt_4, 32768, 256, grid=grid(32768), stream=stream0)
        del add_9
        del rsqrt_4
        buf156 = buf129; del buf129  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf154, (32768, 256), (256, 1), 0), permute_149, out=buf156)
        del permute_149
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._scaled_dot_product_flash_attention_backward]
        buf158 = torch.ops.aten._scaled_dot_product_flash_attention_backward.default(reinterpret_tensor(buf156, (16, 2, 2048, 128), (524288, 128, 256, 1), 0), permute_3, permute_4, permute_5, getitem, getitem_1, None, None, 2048, 2048, 0.0, True, getitem_6, getitem_7, scale=0.08838834764831843)
        del getitem_1
        del getitem_6
        del getitem_7
        del permute_3
        del permute_4
        del permute_5
        buf161 = buf158[2]
        buf169 = buf156; del buf156  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf161, (32768, 256), (256, 1), 0), permute_157, out=buf169)
        del permute_157
        buf159 = buf158[0]
        buf160 = buf158[1]
        del buf158
        buf162 = empty_strided_cuda((16, 2048, 2, 1), (4096, 2, 1, 65536), torch.float32)
        # Topologically Sorted Source Nodes: [k_2], Original ATen: [aten._to_copy, aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_mul_sum_7.run(buf160, cat_1, buf162, 65536, 128, grid=grid(65536), stream=stream0)
        buf163 = empty_strided_cuda((16, 2048, 2, 1), (4096, 2, 1, 65536), torch.float32)
        # Topologically Sorted Source Nodes: [q_2], Original ATen: [aten._to_copy, aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_mul_sum_7.run(buf159, cat, buf163, 65536, 128, grid=grid(65536), stream=stream0)
        buf164 = buf118; del buf118  # reuse
        buf165 = buf117; del buf117  # reuse
        buf166 = buf116; del buf116  # reuse
        buf167 = buf115; del buf115  # reuse
        # Topologically Sorted Source Nodes: [neg], Original ATen: [aten.neg, aten.mul, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_mul_neg_8.run(buf160, rsqrt_3, buf162, cat_1, slice_2, slice_4, buf159, rsqrt_2, buf163, cat, buf164, buf165, buf166, buf167, 4194304, grid=grid(4194304), stream=stream0)
        del cat
        del cat_1
        del rsqrt_2
        del rsqrt_3
        del slice_2
        del slice_4
        buf171 = reinterpret_tensor(buf160, (16, 2048, 2, 128), (524288, 256, 128, 1), 0); del buf160  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.slice_backward, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_slice_backward_11.run(buf164, buf165, buf171, 8388608, grid=grid(8388608), stream=stream0)
        del buf164
        del buf165
        buf173 = reinterpret_tensor(buf159, (32768, 256), (256, 1), 0); del buf159  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf171, (32768, 256), (256, 1), 0), permute_161, out=buf173)
        del permute_161
        buf175 = reinterpret_tensor(buf72, (16, 2048, 2, 128), (524288, 256, 128, 1), 0); del buf72  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.slice_backward, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_slice_backward_11.run(buf166, buf167, buf175, 8388608, grid=grid(8388608), stream=stream0)
        del buf166
        del buf167
        buf177 = reinterpret_tensor(buf65, (32768, 256), (256, 1), 0); del buf65  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf175, (32768, 256), (256, 1), 0), permute_165, out=buf177)
        del permute_165
        buf141 = buf94; del buf94  # reuse
        buf143 = buf92; del buf92  # reuse
        buf183 = buf16; del buf16  # reuse
        buf181 = buf54; del buf54  # reuse
        buf138 = buf49; del buf49  # reuse
        buf187 = empty_strided_cuda((16, 2048, 256), (524288, 256, 1), torch.float32)
        # Topologically Sorted Source Nodes: [loss, x_1, mul, mul_1, x_2, rms_norm_1], Original ATen: [aten.nll_loss_forward, aten.add, aten.mul, aten._to_copy, aten.embedding_dense_backward, aten.sum, aten.div, aten.pow]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_div_embedding_dense_backward_mul_nll_loss_forward_pow_sum_21.run(buf183, buf105, buf136, embedding, rsqrt, add_11, buf169, buf173, buf177, primals_5, primals_6, rsqrt_1, buf47, buf91, buf154, primals_1, buf112, mm_9, buf141, buf143, buf181, buf138, buf187, 32768, 256, grid=grid(32768), stream=stream0)
        del add_11
        del buf105
        del buf112
        del buf136
        del buf169
        del buf173
        del buf177
        del buf183
        del buf47
        del buf91
        del embedding
        del mm_9
        del primals_5
        del primals_6
        del rsqrt
        del rsqrt_1
        aten.index_put_(buf137, [primals_1], buf138, True)
        del buf138
        buf140 = empty_strided_cuda((8192, 256), (256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.embedding_dense_backward]
        stream0 = get_raw_stream(0)
        triton_poi_fused_embedding_dense_backward_14.run(buf137, buf140, 2097152, grid=grid(2097152), stream=stream0)
        buf142 = empty_strided_cuda((), (), torch.float32)
        # Topologically Sorted Source Nodes: [x_1], Original ATen: [aten._to_copy, aten.mul, aten.add, aten.sum]
        stream0 = get_raw_stream(0)
        triton_red_fused__to_copy_add_mul_sum_17.run(buf141, buf142, 1, 32768, grid=grid(1), stream=stream0)
        del buf141
        buf144 = empty_strided_cuda((), (), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.add, aten.mul, aten.sum]
        stream0 = get_raw_stream(0)
        triton_red_fused__to_copy_add_mul_sum_17.run(buf143, buf144, 1, 32768, grid=grid(1), stream=stream0)
        del buf143
        buf146 = reinterpret_tensor(buf101, (256, 1024), (1024, 1), 0); del buf101  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf145, (256, 32768), (1, 256), 0), view_16, out=buf146)
        del buf145
        del view_16
        buf148 = empty_strided_cuda((256, 1024), (1024, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_3.run(buf146, buf148, 262144, grid=grid(262144), stream=stream0)
        buf150 = reinterpret_tensor(buf146, (1024, 256), (256, 1), 0); del buf146  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf149, (1024, 32768), (1, 1024), 0), view_14, out=buf150)
        del buf149
        del view_14
        buf152 = empty_strided_cuda((1024, 256), (256, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_3.run(buf150, buf152, 262144, grid=grid(262144), stream=stream0)
        del buf150
        buf155 = buf132; del buf132  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf154, (256, 32768), (1, 256), 0), reinterpret_tensor(getitem, (32768, 256), (256, 1), 0), out=buf155)
        del buf154
        del getitem
        buf157 = reinterpret_tensor(buf163, (256, 256), (256, 1), 0); del buf163  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf155, buf157, 65536, grid=grid(65536), stream=stream0)
        buf168 = buf155; del buf155  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf161, (256, 32768), (1, 256), 0), view, out=buf168)
        del buf161
        buf170 = reinterpret_tensor(buf162, (256, 256), (256, 1), 0); del buf162  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf168, buf170, 65536, grid=grid(65536), stream=stream0)
        buf172 = buf168; del buf168  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf171, (256, 32768), (1, 256), 0), view, out=buf172)
        del buf171
        buf174 = empty_strided_cuda((256, 256), (256, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf172, buf174, 65536, grid=grid(65536), stream=stream0)
        buf176 = buf172; del buf172  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf175, (256, 32768), (1, 256), 0), view, out=buf176)
        del buf175
        del view
        buf178 = empty_strided_cuda((256, 256), (256, 1), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_6.run(buf176, buf178, 65536, grid=grid(65536), stream=stream0)
        del buf176
        buf182 = empty_strided_cuda((), (), torch.float32)
        # Topologically Sorted Source Nodes: [x_1], Original ATen: [aten._to_copy, aten.mul, aten.add, aten.sum]
        stream0 = get_raw_stream(0)
        triton_red_fused__to_copy_add_mul_sum_17.run(buf181, buf182, 1, 32768, grid=grid(1), stream=stream0)
        del buf181
        buf184 = empty_strided_cuda((4, ), (1, ), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.select_backward, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_select_backward_22.run(buf53, buf93, buf142, buf182, buf184, 4, grid=grid(4), stream=stream0)
        del buf142
        del buf53
        del buf93
        buf185 = empty_strided_cuda((4, ), (1, ), torch.float32)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.select_backward, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_select_backward_22.run(buf55, buf95, buf144, buf182, buf185, 4, grid=grid(4), stream=stream0)
        del buf144
        del buf182
        del buf55
        del buf95
        buf188 = buf137; del buf137  # reuse
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.embedding_dense_backward]
        stream0 = get_raw_stream(0)
        triton_poi_fused_embedding_dense_backward_nll_loss_forward_13.run(buf188, 2097152, grid=grid(2097152), stream=stream0)
        aten.index_put_(buf188, [primals_1], buf187, True)
        del buf187
        del primals_1
        buf190 = empty_strided_cuda((8192, 256), (256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [], Original ATen: [aten.embedding_dense_backward]
        stream0 = get_raw_stream(0)
        triton_poi_fused_embedding_dense_backward_14.run(buf188, buf190, 2097152, grid=grid(2097152), stream=stream0)
        del buf188
    return (None, None, None, buf190, buf185, buf184, buf178, buf174, buf170, buf157, buf152, buf148, buf140, buf134, buf130, buf126, buf123, buf108, buf103, buf99, buf89, buf85, buf81, buf68, buf63, buf59, buf51, buf45, buf41, buf37, buf34, buf19, buf14, buf10, buf5, None, )


def benchmark_compiled_module(times=10, repeat=10):
    from torch._dynamo.testing import rand_strided
    from torch._inductor.utils import print_performance
    primals_1 = rand_strided((16, 2048), (2048, 1), device='cuda:0', dtype=torch.int64)
    primals_5 = rand_strided((4, ), (1, ), device='cuda:0', dtype=torch.float32)
    primals_6 = rand_strided((4, ), (1, ), device='cuda:0', dtype=torch.float32)
    primals_36 = rand_strided((16, 2048), (2048, 1), device='cuda:0', dtype=torch.int64)
    slice_2 = rand_strided((1, 2048, 1, 64), (1310720, 64, 64, 1), device='cuda:0', dtype=torch.bfloat16)
    slice_4 = rand_strided((1, 2048, 1, 64), (1310720, 64, 64, 1), device='cuda:0', dtype=torch.bfloat16)
    embedding = rand_strided((16, 2048, 256), (524288, 256, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt = rand_strided((16, 2048, 1), (2048, 1, 1), device='cuda:0', dtype=torch.float32)
    rsqrt_1 = rand_strided((16, 2048, 1), (2048, 1, 1), device='cuda:0', dtype=torch.float32)
    view = rand_strided((32768, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    cat = rand_strided((16, 2048, 2, 128), (524288, 256, 128, 1), device='cuda:0', dtype=torch.bfloat16)
    cat_1 = rand_strided((16, 2048, 2, 128), (524288, 256, 128, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt_2 = rand_strided((16, 2048, 2, 1), (4096, 2, 1, 1), device='cuda:0', dtype=torch.float32)
    rsqrt_3 = rand_strided((16, 2048, 2, 1), (4096, 2, 1, 1), device='cuda:0', dtype=torch.float32)
    permute_3 = rand_strided((16, 2, 2048, 128), (524288, 128, 256, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_4 = rand_strided((16, 2, 2048, 128), (524288, 128, 256, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_5 = rand_strided((16, 2, 2048, 128), (524288, 128, 256, 1), device='cuda:0', dtype=torch.bfloat16)
    getitem = rand_strided((16, 2, 2048, 128), (524288, 128, 256, 1), device='cuda:0', dtype=torch.bfloat16)
    getitem_1 = rand_strided((16, 2, 2048), (4096, 2048, 1), device='cuda:0', dtype=torch.float32)
    getitem_6 = rand_strided((), (), device='cuda:0', dtype=torch.int64)
    getitem_7 = rand_strided((), (), device='cuda:0', dtype=torch.int64)
    add_9 = rand_strided((16, 2048, 256), (524288, 256, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt_4 = rand_strided((16, 2048, 1), (2048, 1, 1), device='cuda:0', dtype=torch.float32)
    view_14 = rand_strided((32768, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    mm_4 = rand_strided((32768, 1024), (1024, 1), device='cuda:0', dtype=torch.bfloat16)
    view_16 = rand_strided((32768, 1024), (1024, 1), device='cuda:0', dtype=torch.bfloat16)
    add_11 = rand_strided((16, 2048, 256), (524288, 256, 1), device='cuda:0', dtype=torch.bfloat16)
    add_12 = rand_strided((16, 2048, 256), (524288, 256, 1), device='cuda:0', dtype=torch.bfloat16)
    embedding_1 = rand_strided((16, 2048, 256), (524288, 256, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt_5 = rand_strided((16, 2048, 1), (2048, 1, 1), device='cuda:0', dtype=torch.float32)
    view_18 = rand_strided((32768, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    view_28 = rand_strided((32768, 32), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    mm_9 = rand_strided((32768, 2), (2, 1), device='cuda:0', dtype=torch.bfloat16)
    cat_2 = rand_strided((16, 2048, 2, 128), (524288, 256, 128, 1), device='cuda:0', dtype=torch.bfloat16)
    cat_3 = rand_strided((16, 2048, 2, 128), (524288, 256, 128, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt_6 = rand_strided((16, 2048, 2, 1), (4096, 2, 1, 1), device='cuda:0', dtype=torch.float32)
    rsqrt_7 = rand_strided((16, 2048, 2, 1), (4096, 2, 1, 1), device='cuda:0', dtype=torch.float32)
    permute_14 = rand_strided((16, 2, 2048, 128), (524288, 128, 256, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_15 = rand_strided((16, 2, 2048, 128), (524288, 128, 256, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_16 = rand_strided((16, 2, 2048, 128), (524288, 128, 256, 1), device='cuda:0', dtype=torch.bfloat16)
    getitem_9 = rand_strided((16, 2, 2048, 128), (524288, 128, 256, 1), device='cuda:0', dtype=torch.bfloat16)
    getitem_10 = rand_strided((16, 2, 2048), (4096, 2048, 1), device='cuda:0', dtype=torch.float32)
    getitem_15 = rand_strided((), (), device='cuda:0', dtype=torch.int64)
    getitem_16 = rand_strided((), (), device='cuda:0', dtype=torch.int64)
    add_21 = rand_strided((16, 2048, 256), (524288, 256, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt_8 = rand_strided((16, 2048, 1), (2048, 1, 1), device='cuda:0', dtype=torch.float32)
    view_35 = rand_strided((32768, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    mm_11 = rand_strided((32768, 1024), (1024, 1), device='cuda:0', dtype=torch.bfloat16)
    view_37 = rand_strided((32768, 1024), (1024, 1), device='cuda:0', dtype=torch.bfloat16)
    add_23 = rand_strided((16, 2048, 256), (524288, 256, 1), device='cuda:0', dtype=torch.bfloat16)
    add_24 = rand_strided((16, 2048, 256), (524288, 256, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt_9 = rand_strided((16, 2048, 1), (2048, 1, 1), device='cuda:0', dtype=torch.float32)
    view_39 = rand_strided((32768, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    cat_4 = rand_strided((16, 2048, 2, 128), (524288, 256, 128, 1), device='cuda:0', dtype=torch.bfloat16)
    cat_5 = rand_strided((16, 2048, 2, 128), (524288, 256, 128, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt_10 = rand_strided((16, 2048, 2, 1), (4096, 2, 1, 1), device='cuda:0', dtype=torch.float32)
    rsqrt_11 = rand_strided((16, 2048, 2, 1), (4096, 2, 1, 1), device='cuda:0', dtype=torch.float32)
    permute_24 = rand_strided((16, 2, 2048, 128), (524288, 128, 256, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_25 = rand_strided((16, 2, 2048, 128), (524288, 128, 256, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_26 = rand_strided((16, 2, 2048, 128), (524288, 128, 256, 1), device='cuda:0', dtype=torch.bfloat16)
    getitem_18 = rand_strided((16, 2, 2048, 128), (524288, 128, 256, 1), device='cuda:0', dtype=torch.bfloat16)
    getitem_19 = rand_strided((16, 2, 2048), (4096, 2048, 1), device='cuda:0', dtype=torch.float32)
    getitem_24 = rand_strided((), (), device='cuda:0', dtype=torch.int64)
    getitem_25 = rand_strided((), (), device='cuda:0', dtype=torch.int64)
    add_32 = rand_strided((16, 2048, 256), (524288, 256, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt_12 = rand_strided((16, 2048, 1), (2048, 1, 1), device='cuda:0', dtype=torch.float32)
    view_53 = rand_strided((32768, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    mm_17 = rand_strided((32768, 1024), (1024, 1), device='cuda:0', dtype=torch.bfloat16)
    view_55 = rand_strided((32768, 1024), (1024, 1), device='cuda:0', dtype=torch.bfloat16)
    add_34 = rand_strided((16, 2048, 256), (524288, 256, 1), device='cuda:0', dtype=torch.bfloat16)
    add_35 = rand_strided((16, 2048, 256), (524288, 256, 1), device='cuda:0', dtype=torch.bfloat16)
    embedding_2 = rand_strided((16, 2048, 256), (524288, 256, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt_13 = rand_strided((16, 2048, 1), (2048, 1, 1), device='cuda:0', dtype=torch.float32)
    view_57 = rand_strided((32768, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    view_67 = rand_strided((32768, 32), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    mm_22 = rand_strided((32768, 2), (2, 1), device='cuda:0', dtype=torch.bfloat16)
    cat_6 = rand_strided((16, 2048, 2, 128), (524288, 256, 128, 1), device='cuda:0', dtype=torch.bfloat16)
    cat_7 = rand_strided((16, 2048, 2, 128), (524288, 256, 128, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt_14 = rand_strided((16, 2048, 2, 1), (4096, 2, 1, 1), device='cuda:0', dtype=torch.float32)
    rsqrt_15 = rand_strided((16, 2048, 2, 1), (4096, 2, 1, 1), device='cuda:0', dtype=torch.float32)
    permute_35 = rand_strided((16, 2, 2048, 128), (524288, 128, 256, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_36 = rand_strided((16, 2, 2048, 128), (524288, 128, 256, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_37 = rand_strided((16, 2, 2048, 128), (524288, 128, 256, 1), device='cuda:0', dtype=torch.bfloat16)
    getitem_27 = rand_strided((16, 2, 2048, 128), (524288, 128, 256, 1), device='cuda:0', dtype=torch.bfloat16)
    getitem_28 = rand_strided((16, 2, 2048), (4096, 2048, 1), device='cuda:0', dtype=torch.float32)
    getitem_33 = rand_strided((), (), device='cuda:0', dtype=torch.int64)
    getitem_34 = rand_strided((), (), device='cuda:0', dtype=torch.int64)
    add_44 = rand_strided((16, 2048, 256), (524288, 256, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt_16 = rand_strided((16, 2048, 1), (2048, 1, 1), device='cuda:0', dtype=torch.float32)
    view_74 = rand_strided((32768, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    mm_24 = rand_strided((32768, 1024), (1024, 1), device='cuda:0', dtype=torch.bfloat16)
    view_76 = rand_strided((32768, 1024), (1024, 1), device='cuda:0', dtype=torch.bfloat16)
    add_46 = rand_strided((16, 2048, 256), (524288, 256, 1), device='cuda:0', dtype=torch.bfloat16)
    rsqrt_17 = rand_strided((16, 2048, 1), (2048, 1, 1), device='cuda:0', dtype=torch.float32)
    view_78 = rand_strided((32768, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    mm_26 = rand_strided((32768, 8192), (8192, 1), device='cuda:0', dtype=torch.bfloat16)
    amax = rand_strided((32768, 1), (1, 1), device='cuda:0', dtype=torch.float32)
    log = rand_strided((32768, 1), (1, 1), device='cuda:0', dtype=torch.float32)
    convert_element_type_126 = rand_strided((), (), device='cuda:0', dtype=torch.float32)
    permute_45 = rand_strided((8192, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_49 = rand_strided((256, 1024), (1024, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_53 = rand_strided((1024, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_57 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_65 = rand_strided((2, 32), (32, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_69 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_73 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_77 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_81 = rand_strided((256, 1024), (1024, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_85 = rand_strided((1024, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_89 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_97 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_101 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_105 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_109 = rand_strided((256, 1024), (1024, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_113 = rand_strided((1024, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_117 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_125 = rand_strided((2, 32), (32, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_129 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_133 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_137 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_141 = rand_strided((256, 1024), (1024, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_145 = rand_strided((1024, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_149 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_157 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_161 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    permute_165 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    tangents_1 = rand_strided((), (), device='cuda:0', dtype=torch.float32)
    fn = lambda: call([primals_1, primals_5, primals_6, primals_36, slice_2, slice_4, embedding, rsqrt, rsqrt_1, view, cat, cat_1, rsqrt_2, rsqrt_3, permute_3, permute_4, permute_5, getitem, getitem_1, getitem_6, getitem_7, add_9, rsqrt_4, view_14, mm_4, view_16, add_11, add_12, embedding_1, rsqrt_5, view_18, view_28, mm_9, cat_2, cat_3, rsqrt_6, rsqrt_7, permute_14, permute_15, permute_16, getitem_9, getitem_10, getitem_15, getitem_16, add_21, rsqrt_8, view_35, mm_11, view_37, add_23, add_24, rsqrt_9, view_39, cat_4, cat_5, rsqrt_10, rsqrt_11, permute_24, permute_25, permute_26, getitem_18, getitem_19, getitem_24, getitem_25, add_32, rsqrt_12, view_53, mm_17, view_55, add_34, add_35, embedding_2, rsqrt_13, view_57, view_67, mm_22, cat_6, cat_7, rsqrt_14, rsqrt_15, permute_35, permute_36, permute_37, getitem_27, getitem_28, getitem_33, getitem_34, add_44, rsqrt_16, view_74, mm_24, view_76, add_46, rsqrt_17, view_78, mm_26, amax, log, convert_element_type_126, permute_45, permute_49, permute_53, permute_57, permute_65, permute_69, permute_73, permute_77, permute_81, permute_85, permute_89, permute_97, permute_101, permute_105, permute_109, permute_113, permute_117, permute_125, permute_129, permute_133, permute_137, permute_141, permute_145, permute_149, permute_157, permute_161, permute_165, tangents_1])
    return print_performance(fn, times=times, repeat=repeat)


if __name__ == "__main__":
    from torch._inductor.wrapper_benchmark import compiled_module_main
    compiled_module_main('None', benchmark_compiled_module)
