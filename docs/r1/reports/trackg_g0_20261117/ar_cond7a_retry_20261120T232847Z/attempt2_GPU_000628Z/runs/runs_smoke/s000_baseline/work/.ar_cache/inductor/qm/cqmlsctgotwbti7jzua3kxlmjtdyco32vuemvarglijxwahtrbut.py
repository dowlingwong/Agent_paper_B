# AOT ID: ['5_inference']
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


# kernel path: /home/dowling/r1_engineering/u2_iso_20261119/ar_cond7a_retry_20261120T232847Z/attempt2_GPU_000628Z/runs/runs_smoke/s000_baseline/work/.ar_cache/inductor/ag/cagalv5b66ul3yd2egpvfftqxs7wtcpi5addffbgxc4h5dfaiw5b.py
# Topologically Sorted Source Nodes: [g, sub, lerp_, X, norm], Original ATen: [aten.lerp, aten.rsub, aten._to_copy, aten.linalg_vector_norm]
# Source node to ATen node mapping:
#   X => convert_element_type_4
#   g => abs_2, add_1, ge_1, mul_1, sub_3, sub_4, where_2, where_3
#   lerp_ => abs_1, add, ge, mul, sub_1, sub_2, where, where_1
#   norm => convert_element_type_5, pow_1, sum_1
#   sub => sub
# Graph fragment:
#   %abs_2 : [num_users=1] = call_function[target=torch.ops.aten.abs.default](args = (%device_put,), kwargs = {})
#   %ge_1 : [num_users=2] = call_function[target=torch.ops.aten.ge.Scalar](args = (%abs_2, 0.5), kwargs = {})
#   %sub_3 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (%device_put, 1), kwargs = {})
#   %where_2 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%ge_1, %sub_3, %device_put), kwargs = {})
#   %sub : [num_users=3] = call_function[target=torch.ops.aten.sub.Tensor](args = (1, %device_put), kwargs = {})
#   %abs_1 : [num_users=1] = call_function[target=torch.ops.aten.abs.default](args = (%sub,), kwargs = {})
#   %ge : [num_users=2] = call_function[target=torch.ops.aten.ge.Scalar](args = (%abs_1, 0.5), kwargs = {})
#   %sub_1 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (%sub, 1), kwargs = {})
#   %where : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%ge, %sub_1, %sub), kwargs = {})
#   %sub_2 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (%arg5_1, %arg6_1), kwargs = {})
#   %mul : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%where, %sub_2), kwargs = {})
#   %where_1 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%ge, %arg5_1, %arg6_1), kwargs = {})
#   %add : [num_users=3] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul, %where_1), kwargs = {})
#   %sub_4 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (%add, %arg5_1), kwargs = {})
#   %mul_1 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%where_2, %sub_4), kwargs = {})
#   %where_3 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%ge_1, %add, %arg5_1), kwargs = {})
#   %add_1 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_1, %where_3), kwargs = {})
#   %convert_element_type_4 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_1, torch.bfloat16), kwargs = {})
#   %convert_element_type_5 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%convert_element_type_4, torch.float32), kwargs = {})
#   %pow_1 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_5, 2), kwargs = {})
#   %sum_1 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%pow_1, [-2, -1], True), kwargs = {})
triton_red_fused__to_copy_lerp_linalg_vector_norm_rsub_0 = async_compile.triton('triton_red_fused__to_copy_lerp_linalg_vector_norm_rsub_0', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.reduction(
    size_hints={'x': 128, 'r': 8192},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*fp32', 'in_ptr1': '*fp32', 'in_ptr2': '*fp32', 'out_ptr0': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=142, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_red_fused__to_copy_lerp_linalg_vector_norm_rsub_0', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 3, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_red_fused__to_copy_lerp_linalg_vector_norm_rsub_0(in_ptr0, in_ptr1, in_ptr2, out_ptr0, xnumel, rnumel, XBLOCK : tl.constexpr, RBLOCK : tl.constexpr):
    xnumel = 128
    rnumel = 8192
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:, None]
    xmask = xindex < xnumel
    rbase = tl.arange(0, RBLOCK)[None, :]
    tmp0 = tl.load(in_ptr0 + (0))
    tmp1 = tl.broadcast_to(tmp0, [XBLOCK, RBLOCK])
    x0 = xindex
    _tmp27 = tl.full([XBLOCK, RBLOCK], 0, tl.float32)
    for roffset in range(0, rnumel, RBLOCK):
        rindex = roffset + rbase
        rmask = rindex < rnumel
        r1 = rindex
        tmp13 = tl.load(in_ptr1 + (r1 + 8192*x0), rmask & xmask, eviction_policy='evict_first', other=0.0)
        tmp14 = tl.load(in_ptr2 + (r1 + 8192*x0), rmask & xmask, eviction_policy='evict_first', other=0.0)
        tmp2 = tl_math.abs(tmp1)
        tmp3 = 0.5
        tmp4 = tmp2 >= tmp3
        tmp5 = 1.0
        tmp6 = tmp1 - tmp5
        tmp7 = tl.where(tmp4, tmp6, tmp1)
        tmp8 = tmp5 - tmp1
        tmp9 = tl_math.abs(tmp8)
        tmp10 = tmp9 >= tmp3
        tmp11 = tmp8 - tmp5
        tmp12 = tl.where(tmp10, tmp11, tmp8)
        tmp15 = tmp13 - tmp14
        tmp16 = tmp12 * tmp15
        tmp17 = tl.where(tmp10, tmp13, tmp14)
        tmp18 = tmp16 + tmp17
        tmp19 = tmp18 - tmp13
        tmp20 = tmp7 * tmp19
        tmp21 = tl.where(tmp4, tmp18, tmp13)
        tmp22 = tmp20 + tmp21
        tmp23 = tmp22.to(tl.float32)
        tmp24 = tmp23.to(tl.float32)
        tmp25 = tmp24 * tmp24
        tmp26 = tl.broadcast_to(tmp25, [XBLOCK, RBLOCK])
        tmp28 = _tmp27 + tmp26
        _tmp27 = tl.where(rmask & xmask, tmp28, _tmp27)
    tmp27 = tl.sum(_tmp27, 1)[:, None]
    tl.store(out_ptr0 + (x0), tmp27, xmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/u2_iso_20261119/ar_cond7a_retry_20261120T232847Z/attempt2_GPU_000628Z/runs/runs_smoke/s000_baseline/work/.ar_cache/inductor/lk/clkbngq2btodfkxteciegmoenzm45ckkyjfvnt35tr2qprnbwoym.py
# Topologically Sorted Source Nodes: [g, sub, lerp_, X, norm], Original ATen: [aten.lerp, aten.rsub, aten._to_copy, aten.linalg_vector_norm]
# Source node to ATen node mapping:
#   X => convert_element_type_4
#   g => abs_2, add_1, ge_1, mul_1, sub_3, sub_4, where_2, where_3
#   lerp_ => abs_1, add, ge, mul, sub_1, sub_2, where, where_1
#   norm => convert_element_type_5, pow_1, sum_1
#   sub => sub
# Graph fragment:
#   %abs_2 : [num_users=1] = call_function[target=torch.ops.aten.abs.default](args = (%device_put,), kwargs = {})
#   %ge_1 : [num_users=2] = call_function[target=torch.ops.aten.ge.Scalar](args = (%abs_2, 0.5), kwargs = {})
#   %sub_3 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (%device_put, 1), kwargs = {})
#   %where_2 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%ge_1, %sub_3, %device_put), kwargs = {})
#   %sub : [num_users=3] = call_function[target=torch.ops.aten.sub.Tensor](args = (1, %device_put), kwargs = {})
#   %abs_1 : [num_users=1] = call_function[target=torch.ops.aten.abs.default](args = (%sub,), kwargs = {})
#   %ge : [num_users=2] = call_function[target=torch.ops.aten.ge.Scalar](args = (%abs_1, 0.5), kwargs = {})
#   %sub_1 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (%sub, 1), kwargs = {})
#   %where : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%ge, %sub_1, %sub), kwargs = {})
#   %sub_2 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (%arg5_1, %arg6_1), kwargs = {})
#   %mul : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%where, %sub_2), kwargs = {})
#   %where_1 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%ge, %arg5_1, %arg6_1), kwargs = {})
#   %add : [num_users=3] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul, %where_1), kwargs = {})
#   %sub_4 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (%add, %arg5_1), kwargs = {})
#   %mul_1 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%where_2, %sub_4), kwargs = {})
#   %where_3 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%ge_1, %add, %arg5_1), kwargs = {})
#   %add_1 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_1, %where_3), kwargs = {})
#   %convert_element_type_4 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_1, torch.bfloat16), kwargs = {})
#   %convert_element_type_5 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%convert_element_type_4, torch.float32), kwargs = {})
#   %pow_1 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_5, 2), kwargs = {})
#   %sum_1 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%pow_1, [-2, -1], True), kwargs = {})
triton_per_fused__to_copy_lerp_linalg_vector_norm_rsub_1 = async_compile.triton('triton_per_fused__to_copy_lerp_linalg_vector_norm_rsub_1', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 16, 'r': 8},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*fp32', 'out_ptr0': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=142, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_lerp_linalg_vector_norm_rsub_1', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 1, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_lerp_linalg_vector_norm_rsub_1(in_ptr0, out_ptr0, xnumel, rnumel, XBLOCK : tl.constexpr):
    xnumel = 16
    rnumel = 8
    RBLOCK: tl.constexpr = 8
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:, None]
    xmask = xindex < xnumel
    rindex = tl.arange(0, RBLOCK)[None, :]
    roffset = 0
    rmask = tl.full([XBLOCK, RBLOCK], True, tl.int1)
    r1 = rindex
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (r1 + 8*x0), xmask, other=0.0)
    tmp1 = tl.broadcast_to(tmp0, [XBLOCK, RBLOCK])
    tmp3 = tl.where(xmask, tmp1, 0)
    tmp4 = tl.sum(tmp3, 1)[:, None]
    tl.store(out_ptr0 + (x0), tmp4, xmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/u2_iso_20261119/ar_cond7a_retry_20261120T232847Z/attempt2_GPU_000628Z/runs/runs_smoke/s000_baseline/work/.ar_cache/inductor/gt/cgt3ys4hicboqht6eslzl67ekciyx5757dolxayakzb7xjghxjfr.py
# Topologically Sorted Source Nodes: [g, sub, lerp_, X, norm, mul, add, X_1], Original ATen: [aten.lerp, aten.rsub, aten._to_copy, aten.linalg_vector_norm, aten.mul, aten.add, aten.div]
# Source node to ATen node mapping:
#   X => convert_element_type_4
#   X_1 => div
#   add => add_2
#   g => abs_2, add_1, ge_1, mul_1, sub_3, sub_4, where_2, where_3
#   lerp_ => abs_1, add, ge, mul, sub_1, sub_2, where, where_1
#   mul => mul_2
#   norm => convert_element_type_6, pow_2
#   sub => sub
# Graph fragment:
#   %abs_2 : [num_users=1] = call_function[target=torch.ops.aten.abs.default](args = (%device_put,), kwargs = {})
#   %ge_1 : [num_users=2] = call_function[target=torch.ops.aten.ge.Scalar](args = (%abs_2, 0.5), kwargs = {})
#   %sub_3 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (%device_put, 1), kwargs = {})
#   %where_2 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%ge_1, %sub_3, %device_put), kwargs = {})
#   %sub : [num_users=3] = call_function[target=torch.ops.aten.sub.Tensor](args = (1, %device_put), kwargs = {})
#   %abs_1 : [num_users=1] = call_function[target=torch.ops.aten.abs.default](args = (%sub,), kwargs = {})
#   %ge : [num_users=2] = call_function[target=torch.ops.aten.ge.Scalar](args = (%abs_1, 0.5), kwargs = {})
#   %sub_1 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (%sub, 1), kwargs = {})
#   %where : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%ge, %sub_1, %sub), kwargs = {})
#   %sub_2 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (%arg5_1, %arg6_1), kwargs = {})
#   %mul : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%where, %sub_2), kwargs = {})
#   %where_1 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%ge, %arg5_1, %arg6_1), kwargs = {})
#   %add : [num_users=3] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul, %where_1), kwargs = {})
#   %sub_4 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (%add, %arg5_1), kwargs = {})
#   %mul_1 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%where_2, %sub_4), kwargs = {})
#   %where_3 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%ge_1, %add, %arg5_1), kwargs = {})
#   %add_1 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_1, %where_3), kwargs = {})
#   %convert_element_type_4 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_1, torch.bfloat16), kwargs = {})
#   %pow_2 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%sum_1, 0.5), kwargs = {})
#   %convert_element_type_6 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%pow_2, torch.bfloat16), kwargs = {})
#   %mul_2 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_6, 1.02), kwargs = {})
#   %add_2 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_2, 1e-06), kwargs = {})
#   %div : [num_users=4] = call_function[target=torch.ops.aten.div.Tensor](args = (%convert_element_type_4, %add_2), kwargs = {})
#   %copy__1 : [num_users=0] = call_function[target=torch.ops.aten.copy_.default](args = (%arg5_1, %add_1), kwargs = {})
#   %copy__2 : [num_users=0] = call_function[target=torch.ops.aten.copy_.default](args = (%arg6_1, %add), kwargs = {})
triton_poi_fused__to_copy_add_div_lerp_linalg_vector_norm_mul_rsub_2 = async_compile.triton('triton_poi_fused__to_copy_add_div_lerp_linalg_vector_norm_mul_rsub_2', '''
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
    triton_meta={'signature': {'in_ptr0': '*fp32', 'in_ptr1': '*fp32', 'in_ptr2': '*fp32', 'in_ptr3': '*fp32', 'out_ptr0': '*bf16', 'out_ptr3': '*fp32', 'out_ptr4': '*fp32', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=142, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused__to_copy_add_div_lerp_linalg_vector_norm_mul_rsub_2', 'mutated_arg_names': ['in_ptr1', 'in_ptr2', 'out_ptr3', 'out_ptr4'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 4, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused__to_copy_add_div_lerp_linalg_vector_norm_mul_rsub_2(in_ptr0, in_ptr1, in_ptr2, in_ptr3, out_ptr0, out_ptr3, out_ptr4, xnumel, XBLOCK : tl.constexpr):
    xnumel = 1048576
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x2 = xindex
    x1 = xindex // 65536
    tmp0 = tl.load(in_ptr0 + (0))
    tmp1 = tl.broadcast_to(tmp0, [XBLOCK])
    tmp13 = tl.load(in_ptr1 + (x2), None)
    tmp14 = tl.load(in_ptr2 + (x2), None)
    tmp24 = tl.load(in_ptr3 + (x1), None, eviction_policy='evict_last')
    tmp2 = tl_math.abs(tmp1)
    tmp3 = 0.5
    tmp4 = tmp2 >= tmp3
    tmp5 = 1.0
    tmp6 = tmp1 - tmp5
    tmp7 = tl.where(tmp4, tmp6, tmp1)
    tmp8 = tmp5 - tmp1
    tmp9 = tl_math.abs(tmp8)
    tmp10 = tmp9 >= tmp3
    tmp11 = tmp8 - tmp5
    tmp12 = tl.where(tmp10, tmp11, tmp8)
    tmp15 = tmp13 - tmp14
    tmp16 = tmp12 * tmp15
    tmp17 = tl.where(tmp10, tmp13, tmp14)
    tmp18 = tmp16 + tmp17
    tmp19 = tmp18 - tmp13
    tmp20 = tmp7 * tmp19
    tmp21 = tl.where(tmp4, tmp18, tmp13)
    tmp22 = tmp20 + tmp21
    tmp23 = tmp22.to(tl.float32)
    tmp25 = libdevice.sqrt(tmp24)
    tmp26 = tmp25.to(tl.float32)
    tmp27 = 1.02
    tmp28 = tmp26 * tmp27
    tmp29 = 1e-06
    tmp30 = tmp28 + tmp29
    tmp31 = tmp23 / tmp30
    tl.store(out_ptr0 + (x2), tmp31, None)
    tl.store(out_ptr3 + (x2), tmp22, None)
    tl.store(out_ptr4 + (x2), tmp18, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/u2_iso_20261119/ar_cond7a_retry_20261120T232847Z/attempt2_GPU_000628Z/runs/runs_smoke/s000_baseline/work/.ar_cache/inductor/es/cesjwkw6s7bp7zttuypdllhvynb3wqjjm4qlt5k6r2kxijqlozmf.py
# Topologically Sorted Source Nodes: [mul_1, mul_2, B], Original ATen: [aten.mul, aten.add]
# Source node to ATen node mapping:
#   B => add_3
#   mul_1 => mul_3
#   mul_2 => mul_4
# Graph fragment:
#   %mul_3 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%bmm, -22.48329292557795), kwargs = {})
#   %mul_4 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%bmm_1, 15.878769915207462), kwargs = {})
#   %add_3 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_3, %mul_4), kwargs = {})
triton_poi_fused_add_mul_3 = async_compile.triton('triton_poi_fused_add_mul_3', '''
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
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=142, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_add_mul_3', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 2, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_add_mul_3(in_out_ptr0, in_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 1048576
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = xindex
    tmp0 = tl.load(in_out_ptr0 + (x0), None).to(tl.float32)
    tmp3 = tl.load(in_ptr0 + (x0), None).to(tl.float32)
    tmp1 = -22.48329292557795
    tmp2 = tmp0 * tmp1
    tmp4 = 15.878769915207462
    tmp5 = tmp3 * tmp4
    tmp6 = tmp2 + tmp5
    tl.store(in_out_ptr0 + (x0), tmp6, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/u2_iso_20261119/ar_cond7a_retry_20261120T232847Z/attempt2_GPU_000628Z/runs/runs_smoke/s000_baseline/work/.ar_cache/inductor/jr/cjrhslw25mn7f7thjf442o7zr3mtcq46ekokpqtd4j5owinitda4.py
# Topologically Sorted Source Nodes: [mul_3, X_2], Original ATen: [aten.mul, aten.add]
# Source node to ATen node mapping:
#   X_2 => add_4
#   mul_3 => mul_5
# Graph fragment:
#   %mul_5 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%div, 8.156554524902461), kwargs = {})
#   %add_4 : [num_users=4] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_5, %bmm_2), kwargs = {})
triton_poi_fused_add_mul_4 = async_compile.triton('triton_poi_fused_add_mul_4', '''
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
    triton_meta={'signature': {'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'out_ptr0': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=142, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_add_mul_4', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 2, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_add_mul_4(in_ptr0, in_ptr1, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 1048576
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (x0), None).to(tl.float32)
    tmp3 = tl.load(in_ptr1 + (x0), None).to(tl.float32)
    tmp1 = 8.156554524902461
    tmp2 = tmp0 * tmp1
    tmp4 = tmp2 + tmp3
    tl.store(out_ptr0 + (x0), tmp4, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/u2_iso_20261119/ar_cond7a_retry_20261120T232847Z/attempt2_GPU_000628Z/runs/runs_smoke/s000_baseline/work/.ar_cache/inductor/zx/czxy52i2x4qbd3pc5fgtblznosrfzjroyy7amnyn36v5gckmwh22.py
# Topologically Sorted Source Nodes: [mul_4, mul_5, B_1], Original ATen: [aten.mul, aten.add]
# Source node to ATen node mapping:
#   B_1 => add_5
#   mul_4 => mul_6
#   mul_5 => mul_7
# Graph fragment:
#   %mul_6 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%bmm_3, -2.808917465908714), kwargs = {})
#   %mul_7 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%bmm_4, 0.5000178451051316), kwargs = {})
#   %add_5 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_6, %mul_7), kwargs = {})
triton_poi_fused_add_mul_5 = async_compile.triton('triton_poi_fused_add_mul_5', '''
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
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=142, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_add_mul_5', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 2, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_add_mul_5(in_out_ptr0, in_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 1048576
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = xindex
    tmp0 = tl.load(in_out_ptr0 + (x0), None).to(tl.float32)
    tmp3 = tl.load(in_ptr0 + (x0), None).to(tl.float32)
    tmp1 = -2.808917465908714
    tmp2 = tmp0 * tmp1
    tmp4 = 0.5000178451051316
    tmp5 = tmp3 * tmp4
    tmp6 = tmp2 + tmp5
    tl.store(in_out_ptr0 + (x0), tmp6, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/u2_iso_20261119/ar_cond7a_retry_20261120T232847Z/attempt2_GPU_000628Z/runs/runs_smoke/s000_baseline/work/.ar_cache/inductor/nd/cndqbvelxhm4eyfm4ujtzoueywrk6sspurg2x64eo33zi4i6yjgo.py
# Topologically Sorted Source Nodes: [mul_3, X_2, mul_6, X_3], Original ATen: [aten.mul, aten.add]
# Source node to ATen node mapping:
#   X_2 => add_4
#   X_3 => add_6
#   mul_3 => mul_5
#   mul_6 => mul_8
# Graph fragment:
#   %mul_5 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%div, 8.156554524902461), kwargs = {})
#   %add_4 : [num_users=4] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_5, %bmm_2), kwargs = {})
#   %mul_8 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_4, 4.042929935166739), kwargs = {})
#   %add_6 : [num_users=4] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_8, %bmm_5), kwargs = {})
triton_poi_fused_add_mul_6 = async_compile.triton('triton_poi_fused_add_mul_6', '''
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
    triton_meta={'signature': {'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'out_ptr0': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=142, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_add_mul_6', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 3, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_add_mul_6(in_ptr0, in_ptr1, in_ptr2, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 1048576
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (x0), None).to(tl.float32)
    tmp3 = tl.load(in_ptr1 + (x0), None).to(tl.float32)
    tmp7 = tl.load(in_ptr2 + (x0), None).to(tl.float32)
    tmp1 = 8.156554524902461
    tmp2 = tmp0 * tmp1
    tmp4 = tmp2 + tmp3
    tmp5 = 4.042929935166739
    tmp6 = tmp4 * tmp5
    tmp8 = tmp6 + tmp7
    tl.store(out_ptr0 + (x0), tmp8, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/u2_iso_20261119/ar_cond7a_retry_20261120T232847Z/attempt2_GPU_000628Z/runs/runs_smoke/s000_baseline/work/.ar_cache/inductor/6f/c6fxhg45nirlitdub2dr56lse7tttshg3qtkwzzdv7h6qyss4gax.py
# Topologically Sorted Source Nodes: [mul_7, mul_8, B_2], Original ATen: [aten.mul, aten.add]
# Source node to ATen node mapping:
#   B_2 => add_7
#   mul_7 => mul_9
#   mul_8 => mul_10
# Graph fragment:
#   %mul_9 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%bmm_6, -2.772484153217685), kwargs = {})
#   %mul_10 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%bmm_7, 0.5060648178503393), kwargs = {})
#   %add_7 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_9, %mul_10), kwargs = {})
triton_poi_fused_add_mul_7 = async_compile.triton('triton_poi_fused_add_mul_7', '''
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
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=142, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_add_mul_7', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 2, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_add_mul_7(in_out_ptr0, in_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 1048576
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = xindex
    tmp0 = tl.load(in_out_ptr0 + (x0), None).to(tl.float32)
    tmp3 = tl.load(in_ptr0 + (x0), None).to(tl.float32)
    tmp1 = -2.772484153217685
    tmp2 = tmp0 * tmp1
    tmp4 = 0.5060648178503393
    tmp5 = tmp3 * tmp4
    tmp6 = tmp2 + tmp5
    tl.store(in_out_ptr0 + (x0), tmp6, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/u2_iso_20261119/ar_cond7a_retry_20261120T232847Z/attempt2_GPU_000628Z/runs/runs_smoke/s000_baseline/work/.ar_cache/inductor/zm/czmyrbpu5o4tepnnyc2wo6qmztyeid3hojinownunevsggbex36v.py
# Topologically Sorted Source Nodes: [mul_3, X_2, mul_6, X_3, mul_9, X_4], Original ATen: [aten.mul, aten.add]
# Source node to ATen node mapping:
#   X_2 => add_4
#   X_3 => add_6
#   X_4 => add_8
#   mul_3 => mul_5
#   mul_6 => mul_8
#   mul_9 => mul_11
# Graph fragment:
#   %mul_5 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%div, 8.156554524902461), kwargs = {})
#   %add_4 : [num_users=4] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_5, %bmm_2), kwargs = {})
#   %mul_8 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_4, 4.042929935166739), kwargs = {})
#   %add_6 : [num_users=4] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_8, %bmm_5), kwargs = {})
#   %mul_11 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_6, 3.8916678022926607), kwargs = {})
#   %add_8 : [num_users=4] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_11, %bmm_8), kwargs = {})
triton_poi_fused_add_mul_8 = async_compile.triton('triton_poi_fused_add_mul_8', '''
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
    triton_meta={'signature': {'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'in_ptr3': '*bf16', 'out_ptr0': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=142, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_add_mul_8', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 4, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_add_mul_8(in_ptr0, in_ptr1, in_ptr2, in_ptr3, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 1048576
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (x0), None).to(tl.float32)
    tmp3 = tl.load(in_ptr1 + (x0), None).to(tl.float32)
    tmp7 = tl.load(in_ptr2 + (x0), None).to(tl.float32)
    tmp11 = tl.load(in_ptr3 + (x0), None).to(tl.float32)
    tmp1 = 8.156554524902461
    tmp2 = tmp0 * tmp1
    tmp4 = tmp2 + tmp3
    tmp5 = 4.042929935166739
    tmp6 = tmp4 * tmp5
    tmp8 = tmp6 + tmp7
    tmp9 = 3.8916678022926607
    tmp10 = tmp8 * tmp9
    tmp12 = tmp10 + tmp11
    tl.store(out_ptr0 + (x0), tmp12, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/u2_iso_20261119/ar_cond7a_retry_20261120T232847Z/attempt2_GPU_000628Z/runs/runs_smoke/s000_baseline/work/.ar_cache/inductor/7f/c7fcmhr57tjn6j26byzsack3ippunjmu5bysuziy7gcfmfypelth.py
# Topologically Sorted Source Nodes: [mul_10, mul_11, B_3], Original ATen: [aten.mul, aten.add]
# Source node to ATen node mapping:
#   B_3 => add_9
#   mul_10 => mul_12
#   mul_11 => mul_13
# Graph fragment:
#   %mul_12 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%bmm_9, -2.3681294933425376), kwargs = {})
#   %mul_13 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%bmm_10, 0.46449024233003106), kwargs = {})
#   %add_9 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_12, %mul_13), kwargs = {})
triton_poi_fused_add_mul_9 = async_compile.triton('triton_poi_fused_add_mul_9', '''
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
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=142, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_add_mul_9', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 2, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_add_mul_9(in_out_ptr0, in_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 1048576
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = xindex
    tmp0 = tl.load(in_out_ptr0 + (x0), None).to(tl.float32)
    tmp3 = tl.load(in_ptr0 + (x0), None).to(tl.float32)
    tmp1 = -2.3681294933425376
    tmp2 = tmp0 * tmp1
    tmp4 = 0.46449024233003106
    tmp5 = tmp3 * tmp4
    tmp6 = tmp2 + tmp5
    tl.store(in_out_ptr0 + (x0), tmp6, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/u2_iso_20261119/ar_cond7a_retry_20261120T232847Z/attempt2_GPU_000628Z/runs/runs_smoke/s000_baseline/work/.ar_cache/inductor/uq/cuqmqtsznosty4mgfefoomzem3punwb2q7gfdvvbt5oewtvg7ja5.py
# Topologically Sorted Source Nodes: [mul_3, X_2, mul_6, X_3, mul_9, X_4, mul_12, X_5], Original ATen: [aten.mul, aten.add]
# Source node to ATen node mapping:
#   X_2 => add_4
#   X_3 => add_6
#   X_4 => add_8
#   X_5 => add_10
#   mul_12 => mul_14
#   mul_3 => mul_5
#   mul_6 => mul_8
#   mul_9 => mul_11
# Graph fragment:
#   %mul_5 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%div, 8.156554524902461), kwargs = {})
#   %add_4 : [num_users=4] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_5, %bmm_2), kwargs = {})
#   %mul_8 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_4, 4.042929935166739), kwargs = {})
#   %add_6 : [num_users=4] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_8, %bmm_5), kwargs = {})
#   %mul_11 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_6, 3.8916678022926607), kwargs = {})
#   %add_8 : [num_users=4] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_11, %bmm_8), kwargs = {})
#   %mul_14 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_8, 3.285753657755655), kwargs = {})
#   %add_10 : [num_users=4] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_14, %bmm_11), kwargs = {})
triton_poi_fused_add_mul_10 = async_compile.triton('triton_poi_fused_add_mul_10', '''
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
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'in_ptr3': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=142, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_add_mul_10', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 5, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_add_mul_10(in_out_ptr0, in_ptr0, in_ptr1, in_ptr2, in_ptr3, xnumel, XBLOCK : tl.constexpr):
    xnumel = 1048576
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = xindex
    tmp0 = tl.load(in_out_ptr0 + (x0), None).to(tl.float32)
    tmp3 = tl.load(in_ptr0 + (x0), None).to(tl.float32)
    tmp7 = tl.load(in_ptr1 + (x0), None).to(tl.float32)
    tmp11 = tl.load(in_ptr2 + (x0), None).to(tl.float32)
    tmp15 = tl.load(in_ptr3 + (x0), None).to(tl.float32)
    tmp1 = 8.156554524902461
    tmp2 = tmp0 * tmp1
    tmp4 = tmp2 + tmp3
    tmp5 = 4.042929935166739
    tmp6 = tmp4 * tmp5
    tmp8 = tmp6 + tmp7
    tmp9 = 3.8916678022926607
    tmp10 = tmp8 * tmp9
    tmp12 = tmp10 + tmp11
    tmp13 = 3.285753657755655
    tmp14 = tmp12 * tmp13
    tmp16 = tmp14 + tmp15
    tl.store(in_out_ptr0 + (x0), tmp16, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/u2_iso_20261119/ar_cond7a_retry_20261120T232847Z/attempt2_GPU_000628Z/runs/runs_smoke/s000_baseline/work/.ar_cache/inductor/z4/cz4ftjkh7rqgpece7stm7wpzgch467ykekvzc2vji4lfmyizawhf.py
# Topologically Sorted Source Nodes: [mul_13, mul_14, B_4], Original ATen: [aten.mul, aten.add]
# Source node to ATen node mapping:
#   B_4 => add_11
#   mul_13 => mul_15
#   mul_14 => mul_16
# Graph fragment:
#   %mul_15 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%bmm_12, -1.7097828382687081), kwargs = {})
#   %mul_16 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%bmm_13, 0.42323551169305323), kwargs = {})
#   %add_11 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_15, %mul_16), kwargs = {})
triton_poi_fused_add_mul_11 = async_compile.triton('triton_poi_fused_add_mul_11', '''
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
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=142, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_add_mul_11', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 2, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_add_mul_11(in_out_ptr0, in_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 1048576
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = xindex
    tmp0 = tl.load(in_out_ptr0 + (x0), None).to(tl.float32)
    tmp3 = tl.load(in_ptr0 + (x0), None).to(tl.float32)
    tmp1 = -1.7097828382687081
    tmp2 = tmp0 * tmp1
    tmp4 = 0.42323551169305323
    tmp5 = tmp3 * tmp4
    tmp6 = tmp2 + tmp5
    tl.store(in_out_ptr0 + (x0), tmp6, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/u2_iso_20261119/ar_cond7a_retry_20261120T232847Z/attempt2_GPU_000628Z/runs/runs_smoke/s000_baseline/work/.ar_cache/inductor/pu/cpu2am3mflwljjmz7e4iw7dzzokctftqecrma63fewjcp7tsdpk5.py
# Topologically Sorted Source Nodes: [mul_15, X_6, float_1, square, v_mean], Original ATen: [aten.mul, aten.add, aten._to_copy, aten.pow, aten.mean]
# Source node to ATen node mapping:
#   X_6 => add_12
#   float_1 => convert_element_type_38
#   mul_15 => mul_17
#   square => pow_3
#   v_mean => mean
# Graph fragment:
#   %mul_17 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_10, 2.3465413258596377), kwargs = {})
#   %add_12 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_17, %bmm_14), kwargs = {})
#   %convert_element_type_38 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_12, torch.float32), kwargs = {})
#   %pow_3 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_38, 2), kwargs = {})
#   %mean : [num_users=4] = call_function[target=torch.ops.aten.mean.dim](args = (%pow_3, [-1], True), kwargs = {})
triton_per_fused__to_copy_add_mean_mul_pow_12 = async_compile.triton('triton_per_fused__to_copy_add_mean_mul_pow_12', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 4096, 'r': 256},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'out_ptr0': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=142, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_mean_mul_pow_12', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': True, 'num_load': 2, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_mean_mul_pow_12(in_ptr0, in_ptr1, out_ptr0, xnumel, rnumel):
    xnumel = 4096
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
    tmp3 = tl.load(in_ptr1 + (r1 + 256*x0), None).to(tl.float32)
    tmp1 = 2.3465413258596377
    tmp2 = tmp0 * tmp1
    tmp4 = tmp2 + tmp3
    tmp5 = tmp4.to(tl.float32)
    tmp6 = tmp5 * tmp5
    tmp7 = tl.broadcast_to(tmp6, [RBLOCK])
    tmp9 = triton_helpers.promote_to_tensor(tl.sum(tmp7, 0))
    tl.store(out_ptr0 + (x0), tmp9, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/u2_iso_20261119/ar_cond7a_retry_20261120T232847Z/attempt2_GPU_000628Z/runs/runs_smoke/s000_baseline/work/.ar_cache/inductor/7n/c7nehfl2p5k7yutics7e7gpd2qn7xl24odgmuftk2a2ng65g4rts.py
# Topologically Sorted Source Nodes: [mul_15, X_6, float_1, square, v_mean, sum_1, v_norm_sq, v_norm, mul_17, sub_1, lerp__2, clamp_min, step_size, square_1, scaled_sq_sum, sum_2, v_norm_new, clamp_min_1, truediv_1, final_scale, to_8], Original ATen: [aten.mul, aten.add, aten._to_copy, aten.pow, aten.mean, aten.sum, aten.sqrt, aten.rsub, aten.lerp, aten.clamp_min, aten.rsqrt, aten.div]
# Source node to ATen node mapping:
#   X_6 => add_12
#   clamp_min => clamp_min
#   clamp_min_1 => clamp_min_1
#   final_scale => mul_22
#   float_1 => convert_element_type_38
#   lerp__2 => abs_3, add_13, ge_2, mul_19, sub_6, sub_7, where_4, where_5
#   mul_15 => mul_17
#   mul_17 => mul_20
#   scaled_sq_sum => mul_21
#   square => pow_3
#   square_1 => pow_4
#   step_size => rsqrt
#   sub_1 => sub_5
#   sum_1 => sum_2
#   sum_2 => sum_3
#   to_8 => convert_element_type_39
#   truediv_1 => div_1
#   v_mean => mean
#   v_norm => sqrt
#   v_norm_new => sqrt_1
#   v_norm_sq => mul_18
# Graph fragment:
#   %mul_17 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_10, 2.3465413258596377), kwargs = {})
#   %add_12 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_17, %bmm_14), kwargs = {})
#   %convert_element_type_38 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_12, torch.float32), kwargs = {})
#   %pow_3 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_38, 2), kwargs = {})
#   %mean : [num_users=4] = call_function[target=torch.ops.aten.mean.dim](args = (%pow_3, [-1], True), kwargs = {})
#   %sum_2 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mean, [-2, -1], True), kwargs = {})
#   %mul_18 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%sum_2, 256), kwargs = {})
#   %sqrt : [num_users=1] = call_function[target=torch.ops.aten.sqrt.default](args = (%mul_18,), kwargs = {})
#   %mul_20 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%mean, 256), kwargs = {})
#   %sub_5 : [num_users=3] = call_function[target=torch.ops.aten.sub.Tensor](args = (1, %device_put_3), kwargs = {})
#   %abs_3 : [num_users=1] = call_function[target=torch.ops.aten.abs.default](args = (%sub_5,), kwargs = {})
#   %ge_2 : [num_users=2] = call_function[target=torch.ops.aten.ge.Scalar](args = (%abs_3, 0.5), kwargs = {})
#   %sub_6 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (%sub_5, 1), kwargs = {})
#   %where_4 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%ge_2, %sub_6, %sub_5), kwargs = {})
#   %sub_7 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (%mean, %arg7_1), kwargs = {})
#   %mul_19 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%where_4, %sub_7), kwargs = {})
#   %where_5 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%ge_2, %mean, %arg7_1), kwargs = {})
#   %add_13 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_19, %where_5), kwargs = {})
#   %clamp_min : [num_users=1] = call_function[target=torch.ops.aten.clamp_min.default](args = (%add_13, 1e-10), kwargs = {})
#   %rsqrt : [num_users=2] = call_function[target=torch.ops.aten.rsqrt.default](args = (%clamp_min,), kwargs = {})
#   %pow_4 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%rsqrt, 2), kwargs = {})
#   %mul_21 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%mul_20, %pow_4), kwargs = {})
#   %sum_3 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mul_21, [-2, -1], True), kwargs = {})
#   %sqrt_1 : [num_users=1] = call_function[target=torch.ops.aten.sqrt.default](args = (%sum_3,), kwargs = {})
#   %clamp_min_1 : [num_users=1] = call_function[target=torch.ops.aten.clamp_min.default](args = (%sqrt_1, 1e-10), kwargs = {})
#   %div_1 : [num_users=1] = call_function[target=torch.ops.aten.div.Tensor](args = (%sqrt, %clamp_min_1), kwargs = {})
#   %mul_22 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%rsqrt, %div_1), kwargs = {})
#   %convert_element_type_39 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul_22, torch.bfloat16), kwargs = {})
#   %copy__3 : [num_users=0] = call_function[target=torch.ops.aten.copy_.default](args = (%arg7_1, %add_13), kwargs = {})
triton_per_fused__to_copy_add_clamp_min_div_lerp_mean_mul_pow_rsqrt_rsub_sqrt_sum_13 = async_compile.triton('triton_per_fused__to_copy_add_clamp_min_div_lerp_mean_mul_pow_rsqrt_rsub_sqrt_sum_13', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 16, 'r': 256},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*fp32', 'in_ptr1': '*fp32', 'in_ptr2': '*fp32', 'out_ptr2': '*bf16', 'out_ptr4': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=142, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_clamp_min_div_lerp_mean_mul_pow_rsqrt_rsub_sqrt_sum_13', 'mutated_arg_names': ['in_ptr2', 'out_ptr4'], 'optimize_mem': True, 'no_x_dim': True, 'num_load': 3, 'num_reduction': 2, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_clamp_min_div_lerp_mean_mul_pow_rsqrt_rsub_sqrt_sum_13(in_ptr0, in_ptr1, in_ptr2, out_ptr2, out_ptr4, xnumel, rnumel):
    xnumel = 16
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
    tmp0 = tl.load(in_ptr0 + (r1 + 256*x0), None)
    tmp7 = tl.load(in_ptr1 + (0))
    tmp8 = tl.broadcast_to(tmp7, [RBLOCK])
    tmp16 = tl.load(in_ptr2 + (r1 + 256*x0), None)
    tmp1 = 256.0
    tmp2 = tmp0 / tmp1
    tmp3 = tl.broadcast_to(tmp2, [RBLOCK])
    tmp5 = triton_helpers.promote_to_tensor(tl.sum(tmp3, 0))
    tmp6 = tmp2 * tmp1
    tmp9 = 1.0
    tmp10 = tmp9 - tmp8
    tmp11 = tl_math.abs(tmp10)
    tmp12 = 0.5
    tmp13 = tmp11 >= tmp12
    tmp14 = tmp10 - tmp9
    tmp15 = tl.where(tmp13, tmp14, tmp10)
    tmp17 = tmp2 - tmp16
    tmp18 = tmp15 * tmp17
    tmp19 = tl.where(tmp13, tmp2, tmp16)
    tmp20 = tmp18 + tmp19
    tmp21 = 1e-10
    tmp22 = triton_helpers.maximum(tmp20, tmp21)
    tmp23 = libdevice.rsqrt(tmp22)
    tmp24 = tmp23 * tmp23
    tmp25 = tmp6 * tmp24
    tmp26 = tl.broadcast_to(tmp25, [RBLOCK])
    tmp28 = triton_helpers.promote_to_tensor(tl.sum(tmp26, 0))
    tmp29 = tmp5 * tmp1
    tmp30 = libdevice.sqrt(tmp29)
    tmp31 = libdevice.sqrt(tmp28)
    tmp32 = triton_helpers.maximum(tmp31, tmp21)
    tmp33 = tmp30 / tmp32
    tmp34 = tmp23 * tmp33
    tmp35 = tmp34.to(tl.float32)
    tl.store(out_ptr2 + (r1 + 256*x0), tmp35, None)
    tl.store(out_ptr4 + (r1 + 256*x0), tmp20, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/u2_iso_20261119/ar_cond7a_retry_20261120T232847Z/attempt2_GPU_000628Z/runs/runs_smoke/s000_baseline/work/.ar_cache/inductor/dg/cdgtatmdi776v4chfrgqkn6hsdail74lmhfmy35x3qkoe37hzqpx.py
# Topologically Sorted Source Nodes: [lr, mul_15, X_6, float_1, square, v_mean, v_norm_sq, v_norm, sub_1, lerp__2, clamp_min, step_size, v_norm_new, clamp_min_1, truediv_1, final_scale, to_8, g_1, mul_22, wd, mul_23, mul_24, mul_21, mask, mul_25, add_11, sub_], Original ATen: [aten._to_copy, aten.mul, aten.add, aten.pow, aten.mean, aten.sqrt, aten.rsub, aten.lerp, aten.clamp_min, aten.rsqrt, aten.div, aten.ge, aten.sub]
# Source node to ATen node mapping:
#   X_6 => add_12
#   add_11 => add_14
#   clamp_min => clamp_min
#   clamp_min_1 => clamp_min_1
#   final_scale => mul_22
#   float_1 => convert_element_type_38
#   g_1 => mul_23
#   lerp__2 => abs_3, add_13, ge_2, mul_19, sub_6, sub_7, where_4, where_5
#   lr => convert_element_type_40
#   mask => ge_3
#   mul_15 => mul_17
#   mul_21 => mul_24
#   mul_22 => mul_25
#   mul_23 => mul_26
#   mul_24 => mul_27
#   mul_25 => mul_28
#   square => pow_3
#   step_size => rsqrt
#   sub_ => sub_8
#   sub_1 => sub_5
#   to_8 => convert_element_type_39
#   truediv_1 => div_1
#   v_mean => mean
#   v_norm => sqrt
#   v_norm_new => sqrt_1
#   v_norm_sq => mul_18
#   wd => convert_element_type_41
# Graph fragment:
#   %convert_element_type_40 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%device_put_1, torch.bfloat16), kwargs = {})
#   %mul_17 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_10, 2.3465413258596377), kwargs = {})
#   %add_12 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_17, %bmm_14), kwargs = {})
#   %convert_element_type_38 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_12, torch.float32), kwargs = {})
#   %pow_3 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_38, 2), kwargs = {})
#   %mean : [num_users=4] = call_function[target=torch.ops.aten.mean.dim](args = (%pow_3, [-1], True), kwargs = {})
#   %mul_18 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%sum_2, 256), kwargs = {})
#   %sqrt : [num_users=1] = call_function[target=torch.ops.aten.sqrt.default](args = (%mul_18,), kwargs = {})
#   %sub_5 : [num_users=3] = call_function[target=torch.ops.aten.sub.Tensor](args = (1, %device_put_3), kwargs = {})
#   %abs_3 : [num_users=1] = call_function[target=torch.ops.aten.abs.default](args = (%sub_5,), kwargs = {})
#   %ge_2 : [num_users=2] = call_function[target=torch.ops.aten.ge.Scalar](args = (%abs_3, 0.5), kwargs = {})
#   %sub_6 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (%sub_5, 1), kwargs = {})
#   %where_4 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%ge_2, %sub_6, %sub_5), kwargs = {})
#   %sub_7 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (%mean, %arg7_1), kwargs = {})
#   %mul_19 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%where_4, %sub_7), kwargs = {})
#   %where_5 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%ge_2, %mean, %arg7_1), kwargs = {})
#   %add_13 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_19, %where_5), kwargs = {})
#   %clamp_min : [num_users=1] = call_function[target=torch.ops.aten.clamp_min.default](args = (%add_13, 1e-10), kwargs = {})
#   %rsqrt : [num_users=2] = call_function[target=torch.ops.aten.rsqrt.default](args = (%clamp_min,), kwargs = {})
#   %sqrt_1 : [num_users=1] = call_function[target=torch.ops.aten.sqrt.default](args = (%sum_3,), kwargs = {})
#   %clamp_min_1 : [num_users=1] = call_function[target=torch.ops.aten.clamp_min.default](args = (%sqrt_1, 1e-10), kwargs = {})
#   %div_1 : [num_users=1] = call_function[target=torch.ops.aten.div.Tensor](args = (%sqrt, %clamp_min_1), kwargs = {})
#   %mul_22 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%rsqrt, %div_1), kwargs = {})
#   %convert_element_type_39 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul_22, torch.bfloat16), kwargs = {})
#   %mul_23 : [num_users=2] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_12, %convert_element_type_39), kwargs = {})
#   %mul_25 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_40, %mul_23), kwargs = {})
#   %convert_element_type_41 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%device_put_2, torch.bfloat16), kwargs = {})
#   %mul_26 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_40, %convert_element_type_41), kwargs = {})
#   %mul_27 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%mul_26, %arg1_1), kwargs = {})
#   %mul_24 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%mul_23, %arg1_1), kwargs = {})
#   %ge_3 : [num_users=1] = call_function[target=torch.ops.aten.ge.Scalar](args = (%mul_24, 0), kwargs = {})
#   %mul_28 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%mul_27, %ge_3), kwargs = {})
#   %add_14 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_25, %mul_28), kwargs = {})
#   %sub_8 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (%arg1_1, %add_14), kwargs = {})
#   %copy_ : [num_users=0] = call_function[target=torch.ops.aten.copy_.default](args = (%arg1_1, %sub_8), kwargs = {})
triton_poi_fused__to_copy_add_clamp_min_div_ge_lerp_mean_mul_pow_rsqrt_rsub_sqrt_sub_14 = async_compile.triton('triton_poi_fused__to_copy_add_clamp_min_div_ge_lerp_mean_mul_pow_rsqrt_rsub_sqrt_sub_14', '''
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
    triton_meta={'signature': {'in_ptr0': '*fp32', 'in_ptr1': '*fp32', 'in_ptr2': '*bf16', 'in_ptr3': '*bf16', 'in_ptr4': '*bf16', 'in_ptr5': '*fp32', 'out_ptr1': '*fp32', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=142, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused__to_copy_add_clamp_min_div_ge_lerp_mean_mul_pow_rsqrt_rsub_sqrt_sub_14', 'mutated_arg_names': ['in_ptr0', 'out_ptr1'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 6, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused__to_copy_add_clamp_min_div_ge_lerp_mean_mul_pow_rsqrt_rsub_sqrt_sub_14(in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, in_ptr5, out_ptr1, xnumel, XBLOCK : tl.constexpr):
    xnumel = 1048576
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x2 = xindex
    x1 = xindex // 256
    tmp0 = tl.load(in_ptr0 + (x2), None)
    tmp1 = tl.load(in_ptr1 + (0))
    tmp2 = tl.broadcast_to(tmp1, [XBLOCK])
    tmp4 = tl.load(in_ptr2 + (x2), None).to(tl.float32)
    tmp7 = tl.load(in_ptr3 + (x2), None).to(tl.float32)
    tmp9 = tl.load(in_ptr4 + (x1), None, eviction_policy='evict_last').to(tl.float32)
    tmp13 = tl.load(in_ptr5 + (0))
    tmp14 = tl.broadcast_to(tmp13, [XBLOCK])
    tmp3 = tmp2.to(tl.float32)
    tmp5 = 2.3465413258596377
    tmp6 = tmp4 * tmp5
    tmp8 = tmp6 + tmp7
    tmp10 = tmp8 * tmp9
    tmp11 = tmp3 * tmp10
    tmp12 = tmp11.to(tl.float32)
    tmp15 = tmp14.to(tl.float32)
    tmp16 = tmp3 * tmp15
    tmp17 = tmp16.to(tl.float32)
    tmp18 = tmp17 * tmp0
    tmp19 = tmp10.to(tl.float32)
    tmp20 = tmp19 * tmp0
    tmp21 = 0.0
    tmp22 = tmp20 >= tmp21
    tmp23 = tmp22.to(tl.float32)
    tmp24 = tmp18 * tmp23
    tmp25 = tmp12 + tmp24
    tmp26 = tmp0 - tmp25
    tl.store(out_ptr1 + (x2), tmp26, None)
''', device_str='cuda')


async_compile.wait(globals())
del async_compile

def call(args):
    arg0_1, arg1_1, arg2_1, arg3_1, arg4_1, arg5_1, arg6_1, arg7_1 = args
    args.clear()
    assert_size_stride(arg0_1, (), ())
    assert_size_stride(arg1_1, (16, 256, 256), (65536, 256, 1))
    assert_size_stride(arg2_1, (), ())
    assert_size_stride(arg3_1, (), ())
    assert_size_stride(arg4_1, (), ())
    assert_size_stride(arg5_1, (16, 256, 256), (65536, 256, 1))
    assert_size_stride(arg6_1, (16, 256, 256), (65536, 256, 1))
    assert_size_stride(arg7_1, (16, 256, 1), (256, 1, 1))
    with torch.cuda._DeviceGuard(0):
        torch.cuda.set_device(0)
        buf0 = empty_strided_cuda((), (), torch.float32)
        buf0.copy_(arg2_1, False)
        del arg2_1
        buf1 = empty_strided_cuda((), (), torch.float32)
        buf1.copy_(arg0_1, False)
        del arg0_1
        buf2 = empty_strided_cuda((16, 1, 1, 8), (8, 128, 128, 1), torch.float32)
        # Topologically Sorted Source Nodes: [g, sub, lerp_, X, norm], Original ATen: [aten.lerp, aten.rsub, aten._to_copy, aten.linalg_vector_norm]
        stream0 = get_raw_stream(0)
        triton_red_fused__to_copy_lerp_linalg_vector_norm_rsub_0.run(buf1, arg5_1, arg6_1, buf2, 128, 8192, grid=grid(128), stream=stream0)
        buf3 = empty_strided_cuda((16, 1, 1), (1, 16, 16), torch.float32)
        # Topologically Sorted Source Nodes: [g, sub, lerp_, X, norm], Original ATen: [aten.lerp, aten.rsub, aten._to_copy, aten.linalg_vector_norm]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_lerp_linalg_vector_norm_rsub_1.run(buf2, buf3, 16, 8, grid=grid(16), stream=stream0)
        buf4 = empty_strided_cuda((16, 256, 256), (65536, 256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [g, sub, lerp_, X, norm, mul, add, X_1], Original ATen: [aten.lerp, aten.rsub, aten._to_copy, aten.linalg_vector_norm, aten.mul, aten.add, aten.div]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_add_div_lerp_linalg_vector_norm_mul_rsub_2.run(buf1, arg5_1, arg6_1, buf3, buf4, arg5_1, arg6_1, 1048576, grid=grid(1048576), stream=stream0)
        del arg5_1
        del arg6_1
        del buf2
        del buf3
        buf5 = empty_strided_cuda((16, 256, 256), (65536, 256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [A], Original ATen: [aten.bmm]
        extern_kernels.bmm(buf4, reinterpret_tensor(buf4, (16, 256, 256), (65536, 1, 256), 0), out=buf5)
        buf6 = empty_strided_cuda((16, 256, 256), (65536, 256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [matmul_1], Original ATen: [aten.bmm]
        extern_kernels.bmm(buf5, buf5, out=buf6)
        buf7 = buf5; del buf5  # reuse
        # Topologically Sorted Source Nodes: [mul_1, mul_2, B], Original ATen: [aten.mul, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_mul_3.run(buf7, buf6, 1048576, grid=grid(1048576), stream=stream0)
        buf8 = buf6; del buf6  # reuse
        # Topologically Sorted Source Nodes: [mul_1, mul_2, B, matmul_2], Original ATen: [aten.mul, aten.add, aten.bmm]
        extern_kernels.bmm(buf7, buf4, out=buf8)
        buf9 = buf7; del buf7  # reuse
        # Topologically Sorted Source Nodes: [mul_3, X_2], Original ATen: [aten.mul, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_mul_4.run(buf4, buf8, buf9, 1048576, grid=grid(1048576), stream=stream0)
        buf10 = empty_strided_cuda((16, 256, 256), (65536, 256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [mul_3, X_2, A_1], Original ATen: [aten.mul, aten.add, aten.bmm]
        extern_kernels.bmm(buf9, reinterpret_tensor(buf9, (16, 256, 256), (65536, 1, 256), 0), out=buf10)
        buf11 = empty_strided_cuda((16, 256, 256), (65536, 256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [matmul_4], Original ATen: [aten.bmm]
        extern_kernels.bmm(buf10, buf10, out=buf11)
        buf12 = buf10; del buf10  # reuse
        # Topologically Sorted Source Nodes: [mul_4, mul_5, B_1], Original ATen: [aten.mul, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_mul_5.run(buf12, buf11, 1048576, grid=grid(1048576), stream=stream0)
        buf13 = buf11; del buf11  # reuse
        # Topologically Sorted Source Nodes: [mul_4, mul_5, B_1, matmul_5], Original ATen: [aten.mul, aten.add, aten.bmm]
        extern_kernels.bmm(buf12, buf9, out=buf13)
        buf14 = buf9; del buf9  # reuse
        # Topologically Sorted Source Nodes: [mul_3, X_2, mul_6, X_3], Original ATen: [aten.mul, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_mul_6.run(buf4, buf8, buf13, buf14, 1048576, grid=grid(1048576), stream=stream0)
        buf15 = buf12; del buf12  # reuse
        # Topologically Sorted Source Nodes: [mul_3, X_2, mul_6, X_3, A_2], Original ATen: [aten.mul, aten.add, aten.bmm]
        extern_kernels.bmm(buf14, reinterpret_tensor(buf14, (16, 256, 256), (65536, 1, 256), 0), out=buf15)
        buf16 = empty_strided_cuda((16, 256, 256), (65536, 256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [matmul_7], Original ATen: [aten.bmm]
        extern_kernels.bmm(buf15, buf15, out=buf16)
        buf17 = buf15; del buf15  # reuse
        # Topologically Sorted Source Nodes: [mul_7, mul_8, B_2], Original ATen: [aten.mul, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_mul_7.run(buf17, buf16, 1048576, grid=grid(1048576), stream=stream0)
        buf18 = buf16; del buf16  # reuse
        # Topologically Sorted Source Nodes: [mul_7, mul_8, B_2, matmul_8], Original ATen: [aten.mul, aten.add, aten.bmm]
        extern_kernels.bmm(buf17, buf14, out=buf18)
        buf19 = buf17; del buf17  # reuse
        # Topologically Sorted Source Nodes: [mul_3, X_2, mul_6, X_3, mul_9, X_4], Original ATen: [aten.mul, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_mul_8.run(buf4, buf8, buf13, buf18, buf19, 1048576, grid=grid(1048576), stream=stream0)
        buf20 = buf14; del buf14  # reuse
        # Topologically Sorted Source Nodes: [mul_3, X_2, mul_6, X_3, mul_9, X_4, A_3], Original ATen: [aten.mul, aten.add, aten.bmm]
        extern_kernels.bmm(buf19, reinterpret_tensor(buf19, (16, 256, 256), (65536, 1, 256), 0), out=buf20)
        buf21 = empty_strided_cuda((16, 256, 256), (65536, 256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [matmul_10], Original ATen: [aten.bmm]
        extern_kernels.bmm(buf20, buf20, out=buf21)
        buf22 = buf20; del buf20  # reuse
        # Topologically Sorted Source Nodes: [mul_10, mul_11, B_3], Original ATen: [aten.mul, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_mul_9.run(buf22, buf21, 1048576, grid=grid(1048576), stream=stream0)
        buf23 = buf21; del buf21  # reuse
        # Topologically Sorted Source Nodes: [mul_10, mul_11, B_3, matmul_11], Original ATen: [aten.mul, aten.add, aten.bmm]
        extern_kernels.bmm(buf22, buf19, out=buf23)
        del buf19
        del buf22
        buf24 = buf4; del buf4  # reuse
        # Topologically Sorted Source Nodes: [mul_3, X_2, mul_6, X_3, mul_9, X_4, mul_12, X_5], Original ATen: [aten.mul, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_mul_10.run(buf24, buf8, buf13, buf18, buf23, 1048576, grid=grid(1048576), stream=stream0)
        del buf13
        del buf18
        buf25 = buf8; del buf8  # reuse
        # Topologically Sorted Source Nodes: [A_4], Original ATen: [aten.bmm]
        extern_kernels.bmm(buf24, reinterpret_tensor(buf24, (16, 256, 256), (65536, 1, 256), 0), out=buf25)
        buf26 = buf23; del buf23  # reuse
        # Topologically Sorted Source Nodes: [matmul_13], Original ATen: [aten.bmm]
        extern_kernels.bmm(buf25, buf25, out=buf26)
        buf27 = buf25; del buf25  # reuse
        # Topologically Sorted Source Nodes: [mul_13, mul_14, B_4], Original ATen: [aten.mul, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_mul_11.run(buf27, buf26, 1048576, grid=grid(1048576), stream=stream0)
        buf28 = buf26; del buf26  # reuse
        # Topologically Sorted Source Nodes: [mul_13, mul_14, B_4, matmul_14], Original ATen: [aten.mul, aten.add, aten.bmm]
        extern_kernels.bmm(buf27, buf24, out=buf28)
        del buf27
        buf29 = empty_strided_cuda((16, 256, 1), (256, 1, 4096), torch.float32)
        # Topologically Sorted Source Nodes: [mul_15, X_6, float_1, square, v_mean], Original ATen: [aten.mul, aten.add, aten._to_copy, aten.pow, aten.mean]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_mean_mul_pow_12.run(buf24, buf28, buf29, 4096, 256, grid=grid(4096), stream=stream0)
        buf31 = buf1; del buf1  # reuse
        buf31.copy_(arg4_1, False)
        del arg4_1
        buf33 = empty_strided_cuda((16, 256, 1), (256, 1, 4096), torch.bfloat16)
        # Topologically Sorted Source Nodes: [mul_15, X_6, float_1, square, v_mean, sum_1, v_norm_sq, v_norm, mul_17, sub_1, lerp__2, clamp_min, step_size, square_1, scaled_sq_sum, sum_2, v_norm_new, clamp_min_1, truediv_1, final_scale, to_8], Original ATen: [aten.mul, aten.add, aten._to_copy, aten.pow, aten.mean, aten.sum, aten.sqrt, aten.rsub, aten.lerp, aten.clamp_min, aten.rsqrt, aten.div]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_clamp_min_div_lerp_mean_mul_pow_rsqrt_rsub_sqrt_sum_13.run(buf29, buf31, arg7_1, buf33, arg7_1, 16, 256, grid=grid(16), stream=stream0)
        del arg7_1
        del buf29
        buf34 = buf31; del buf31  # reuse
        buf34.copy_(arg3_1, False)
        del arg3_1
        # Topologically Sorted Source Nodes: [lr, mul_15, X_6, float_1, square, v_mean, v_norm_sq, v_norm, sub_1, lerp__2, clamp_min, step_size, v_norm_new, clamp_min_1, truediv_1, final_scale, to_8, g_1, mul_22, wd, mul_23, mul_24, mul_21, mask, mul_25, add_11, sub_], Original ATen: [aten._to_copy, aten.mul, aten.add, aten.pow, aten.mean, aten.sqrt, aten.rsub, aten.lerp, aten.clamp_min, aten.rsqrt, aten.div, aten.ge, aten.sub]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_add_clamp_min_div_ge_lerp_mean_mul_pow_rsqrt_rsub_sqrt_sub_14.run(arg1_1, buf0, buf24, buf28, buf33, buf34, arg1_1, 1048576, grid=grid(1048576), stream=stream0)
        del arg1_1
        del buf0
        del buf24
        del buf28
        del buf33
        del buf34
    return ()


def benchmark_compiled_module(times=10, repeat=10):
    from torch._dynamo.testing import rand_strided
    from torch._inductor.utils import print_performance
    arg0_1 = rand_strided((), (), device='cpu', dtype=torch.float32)
    arg1_1 = rand_strided((16, 256, 256), (65536, 256, 1), device='cuda:0', dtype=torch.float32)
    arg2_1 = rand_strided((), (), device='cpu', dtype=torch.float32)
    arg3_1 = rand_strided((), (), device='cpu', dtype=torch.float32)
    arg4_1 = rand_strided((), (), device='cpu', dtype=torch.float32)
    arg5_1 = rand_strided((16, 256, 256), (65536, 256, 1), device='cuda:0', dtype=torch.float32)
    arg6_1 = rand_strided((16, 256, 256), (65536, 256, 1), device='cuda:0', dtype=torch.float32)
    arg7_1 = rand_strided((16, 256, 1), (256, 1, 1), device='cuda:0', dtype=torch.float32)
    fn = lambda: call([arg0_1, arg1_1, arg2_1, arg3_1, arg4_1, arg5_1, arg6_1, arg7_1])
    return print_performance(fn, times=times, repeat=repeat)


if __name__ == "__main__":
    from torch._inductor.wrapper_benchmark import compiled_module_main
    compiled_module_main('None', benchmark_compiled_module)
