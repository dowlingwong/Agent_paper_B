# AOT ID: ['4_inference']
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


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/q7/cq75tlqckhppa3urxvxt5cxlklkv75jbwhkq7wy2tc7jedr6hzar.py
# Topologically Sorted Source Nodes: [g, sub, lerp_, X, norm, mul, add, X_1], Original ATen: [aten.lerp, aten.rsub, aten._to_copy, aten.linalg_vector_norm, aten.mul, aten.add, aten.div]
# Source node to ATen node mapping:
#   X => convert_element_type_4
#   X_1 => div
#   add => add_2
#   g => abs_2, add_1, ge_1, mul_1, sub_3, sub_4, where_2, where_3
#   lerp_ => abs_1, add, ge, mul, sub_1, sub_2, where, where_1
#   mul => mul_2
#   norm => convert_element_type_5, convert_element_type_6, pow_1, pow_2, sum_1
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
#   %pow_2 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%sum_1, 0.5), kwargs = {})
#   %convert_element_type_6 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%pow_2, torch.bfloat16), kwargs = {})
#   %mul_2 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_6, 1.02), kwargs = {})
#   %add_2 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_2, 1e-06), kwargs = {})
#   %div : [num_users=4] = call_function[target=torch.ops.aten.div.Tensor](args = (%convert_element_type_4, %add_2), kwargs = {})
#   %copy__1 : [num_users=0] = call_function[target=torch.ops.aten.copy_.default](args = (%arg5_1, %add_1), kwargs = {})
#   %copy__2 : [num_users=0] = call_function[target=torch.ops.aten.copy_.default](args = (%arg6_1, %add), kwargs = {})
triton_per_fused__to_copy_add_div_lerp_linalg_vector_norm_mul_rsub_0 = async_compile.triton('triton_per_fused__to_copy_add_div_lerp_linalg_vector_norm_mul_rsub_0', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 4, 'r': 128},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*fp32', 'in_ptr1': '*fp32', 'in_ptr2': '*fp32', 'out_ptr1': '*bf16', 'out_ptr4': '*fp32', 'out_ptr5': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 7), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_div_lerp_linalg_vector_norm_mul_rsub_0', 'mutated_arg_names': ['in_ptr1', 'in_ptr2', 'out_ptr4', 'out_ptr5'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 3, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_div_lerp_linalg_vector_norm_mul_rsub_0(in_ptr0, in_ptr1, in_ptr2, out_ptr1, out_ptr4, out_ptr5, xnumel, rnumel, XBLOCK : tl.constexpr):
    xnumel = 3
    rnumel = 96
    RBLOCK: tl.constexpr = 128
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:, None]
    xmask = xindex < xnumel
    rindex = tl.arange(0, RBLOCK)[None, :]
    roffset = 0
    rmask = rindex < rnumel
    r1 = rindex
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (0))
    tmp1 = tl.broadcast_to(tmp0, [XBLOCK, RBLOCK])
    tmp13 = tl.load(in_ptr1 + (r1 + 96*x0), rmask & xmask, other=0.0)
    tmp14 = tl.load(in_ptr2 + (r1 + 96*x0), rmask & xmask, other=0.0)
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
    tmp28 = tl.where(rmask & xmask, tmp26, 0)
    tmp29 = tl.sum(tmp28, 1)[:, None]
    tmp30 = libdevice.sqrt(tmp29)
    tmp31 = tmp30.to(tl.float32)
    tmp32 = 1.02
    tmp33 = tmp31 * tmp32
    tmp34 = 1e-06
    tmp35 = tmp33 + tmp34
    tmp36 = tmp23 / tmp35
    tl.store(out_ptr1 + (r1 + 96*x0), tmp36, rmask & xmask)
    tl.store(out_ptr4 + (r1 + 96*x0), tmp22, rmask & xmask)
    tl.store(out_ptr5 + (r1 + 96*x0), tmp18, rmask & xmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/cy/ccyg4o4xfdpnizrpaqgkp3a5tgbez2ut4vkqdjblni2yzh7mufty.py
# Topologically Sorted Source Nodes: [mul_1, mul_2, B], Original ATen: [aten.mul, aten.add]
# Source node to ATen node mapping:
#   B => add_3
#   mul_1 => mul_3
#   mul_2 => mul_4
# Graph fragment:
#   %mul_3 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%bmm, -22.48329292557795), kwargs = {})
#   %mul_4 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%bmm_1, 15.878769915207462), kwargs = {})
#   %add_3 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_3, %mul_4), kwargs = {})
triton_poi_fused_add_mul_1 = async_compile.triton('triton_poi_fused_add_mul_1', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.pointwise(
    size_hints={'x': 32}, 
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_add_mul_1', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 2, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_add_mul_1(in_out_ptr0, in_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 27
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = xindex < xnumel
    x0 = xindex
    tmp0 = tl.load(in_out_ptr0 + (x0), xmask).to(tl.float32)
    tmp3 = tl.load(in_ptr0 + (x0), xmask).to(tl.float32)
    tmp1 = -22.48329292557795
    tmp2 = tmp0 * tmp1
    tmp4 = 15.878769915207462
    tmp5 = tmp3 * tmp4
    tmp6 = tmp2 + tmp5
    tl.store(in_out_ptr0 + (x0), tmp6, xmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/ql/cqlrob6kkyv3qtkpk2y7uunbe5sbvldmayp25dhisjmcsfrfokun.py
# Topologically Sorted Source Nodes: [mul_3, X_2], Original ATen: [aten.mul, aten.add]
# Source node to ATen node mapping:
#   X_2 => add_4
#   mul_3 => mul_5
# Graph fragment:
#   %mul_5 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%div, 8.156554524902461), kwargs = {})
#   %add_4 : [num_users=4] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_5, %bmm_2), kwargs = {})
triton_poi_fused_add_mul_2 = async_compile.triton('triton_poi_fused_add_mul_2', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.pointwise(
    size_hints={'x': 512}, 
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'out_ptr0': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_add_mul_2', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 2, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_add_mul_2(in_ptr0, in_ptr1, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 288
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = xindex < xnumel
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (x0), xmask).to(tl.float32)
    tmp3 = tl.load(in_ptr1 + (x0), xmask).to(tl.float32)
    tmp1 = 8.156554524902461
    tmp2 = tmp0 * tmp1
    tmp4 = tmp2 + tmp3
    tl.store(out_ptr0 + (x0), tmp4, xmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/n6/cn6fhbss3n4ghvg66pyb5udr7ztuq2zfsenr7ofiqmo7jkb3touj.py
# Topologically Sorted Source Nodes: [mul_4, mul_5, B_1], Original ATen: [aten.mul, aten.add]
# Source node to ATen node mapping:
#   B_1 => add_5
#   mul_4 => mul_6
#   mul_5 => mul_7
# Graph fragment:
#   %mul_6 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%bmm_3, -2.808917465908714), kwargs = {})
#   %mul_7 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%bmm_4, 0.5000178451051316), kwargs = {})
#   %add_5 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_6, %mul_7), kwargs = {})
triton_poi_fused_add_mul_3 = async_compile.triton('triton_poi_fused_add_mul_3', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.pointwise(
    size_hints={'x': 32}, 
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_add_mul_3', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 2, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_add_mul_3(in_out_ptr0, in_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 27
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = xindex < xnumel
    x0 = xindex
    tmp0 = tl.load(in_out_ptr0 + (x0), xmask).to(tl.float32)
    tmp3 = tl.load(in_ptr0 + (x0), xmask).to(tl.float32)
    tmp1 = -2.808917465908714
    tmp2 = tmp0 * tmp1
    tmp4 = 0.5000178451051316
    tmp5 = tmp3 * tmp4
    tmp6 = tmp2 + tmp5
    tl.store(in_out_ptr0 + (x0), tmp6, xmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/vz/cvzwmx3ctz467rykgiujbmyrljn4nsooyn2quulguj2iayn6s6no.py
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
triton_poi_fused_add_mul_4 = async_compile.triton('triton_poi_fused_add_mul_4', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.pointwise(
    size_hints={'x': 512}, 
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'out_ptr0': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_add_mul_4', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 3, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_add_mul_4(in_ptr0, in_ptr1, in_ptr2, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 288
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = xindex < xnumel
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (x0), xmask).to(tl.float32)
    tmp3 = tl.load(in_ptr1 + (x0), xmask).to(tl.float32)
    tmp7 = tl.load(in_ptr2 + (x0), xmask).to(tl.float32)
    tmp1 = 8.156554524902461
    tmp2 = tmp0 * tmp1
    tmp4 = tmp2 + tmp3
    tmp5 = 4.042929935166739
    tmp6 = tmp4 * tmp5
    tmp8 = tmp6 + tmp7
    tl.store(out_ptr0 + (x0), tmp8, xmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/df/cdfyew4lkzswftmkii2u5o32am5254h2cyjaumzb4lkpmevzwsux.py
# Topologically Sorted Source Nodes: [mul_7, mul_8, B_2], Original ATen: [aten.mul, aten.add]
# Source node to ATen node mapping:
#   B_2 => add_7
#   mul_7 => mul_9
#   mul_8 => mul_10
# Graph fragment:
#   %mul_9 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%bmm_6, -2.772484153217685), kwargs = {})
#   %mul_10 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%bmm_7, 0.5060648178503393), kwargs = {})
#   %add_7 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_9, %mul_10), kwargs = {})
triton_poi_fused_add_mul_5 = async_compile.triton('triton_poi_fused_add_mul_5', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.pointwise(
    size_hints={'x': 32}, 
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_add_mul_5', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 2, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_add_mul_5(in_out_ptr0, in_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 27
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = xindex < xnumel
    x0 = xindex
    tmp0 = tl.load(in_out_ptr0 + (x0), xmask).to(tl.float32)
    tmp3 = tl.load(in_ptr0 + (x0), xmask).to(tl.float32)
    tmp1 = -2.772484153217685
    tmp2 = tmp0 * tmp1
    tmp4 = 0.5060648178503393
    tmp5 = tmp3 * tmp4
    tmp6 = tmp2 + tmp5
    tl.store(in_out_ptr0 + (x0), tmp6, xmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/f4/cf4iahe6tdeq4sqjz3zyh27oqqkwtv2q6vpda6bkv5i6mx3t44d4.py
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
triton_poi_fused_add_mul_6 = async_compile.triton('triton_poi_fused_add_mul_6', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.pointwise(
    size_hints={'x': 512}, 
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'in_ptr3': '*bf16', 'out_ptr0': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_add_mul_6', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 4, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_add_mul_6(in_ptr0, in_ptr1, in_ptr2, in_ptr3, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 288
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = xindex < xnumel
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (x0), xmask).to(tl.float32)
    tmp3 = tl.load(in_ptr1 + (x0), xmask).to(tl.float32)
    tmp7 = tl.load(in_ptr2 + (x0), xmask).to(tl.float32)
    tmp11 = tl.load(in_ptr3 + (x0), xmask).to(tl.float32)
    tmp1 = 8.156554524902461
    tmp2 = tmp0 * tmp1
    tmp4 = tmp2 + tmp3
    tmp5 = 4.042929935166739
    tmp6 = tmp4 * tmp5
    tmp8 = tmp6 + tmp7
    tmp9 = 3.8916678022926607
    tmp10 = tmp8 * tmp9
    tmp12 = tmp10 + tmp11
    tl.store(out_ptr0 + (x0), tmp12, xmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/4a/c4ahben32oqsvqdneksxxnpuf2vvk52rrmbboapyu5d6iyywng72.py
# Topologically Sorted Source Nodes: [mul_10, mul_11, B_3], Original ATen: [aten.mul, aten.add]
# Source node to ATen node mapping:
#   B_3 => add_9
#   mul_10 => mul_12
#   mul_11 => mul_13
# Graph fragment:
#   %mul_12 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%bmm_9, -2.3681294933425376), kwargs = {})
#   %mul_13 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%bmm_10, 0.46449024233003106), kwargs = {})
#   %add_9 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_12, %mul_13), kwargs = {})
triton_poi_fused_add_mul_7 = async_compile.triton('triton_poi_fused_add_mul_7', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.pointwise(
    size_hints={'x': 32}, 
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_add_mul_7', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 2, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_add_mul_7(in_out_ptr0, in_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 27
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = xindex < xnumel
    x0 = xindex
    tmp0 = tl.load(in_out_ptr0 + (x0), xmask).to(tl.float32)
    tmp3 = tl.load(in_ptr0 + (x0), xmask).to(tl.float32)
    tmp1 = -2.3681294933425376
    tmp2 = tmp0 * tmp1
    tmp4 = 0.46449024233003106
    tmp5 = tmp3 * tmp4
    tmp6 = tmp2 + tmp5
    tl.store(in_out_ptr0 + (x0), tmp6, xmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/i7/ci7igdebji3p2i3fkgi3iezlorpmymhmyslxnqykjd3volzx44nx.py
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
triton_poi_fused_add_mul_8 = async_compile.triton('triton_poi_fused_add_mul_8', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.pointwise(
    size_hints={'x': 512}, 
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'in_ptr3': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_add_mul_8', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 5, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_add_mul_8(in_out_ptr0, in_ptr0, in_ptr1, in_ptr2, in_ptr3, xnumel, XBLOCK : tl.constexpr):
    xnumel = 288
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = xindex < xnumel
    x0 = xindex
    tmp0 = tl.load(in_out_ptr0 + (x0), xmask).to(tl.float32)
    tmp3 = tl.load(in_ptr0 + (x0), xmask).to(tl.float32)
    tmp7 = tl.load(in_ptr1 + (x0), xmask).to(tl.float32)
    tmp11 = tl.load(in_ptr2 + (x0), xmask).to(tl.float32)
    tmp15 = tl.load(in_ptr3 + (x0), xmask).to(tl.float32)
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
    tl.store(in_out_ptr0 + (x0), tmp16, xmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/y5/cy5kciktntt2bydkbgms5djmk4qctt6oo34iku6hmimfxyrtkojc.py
# Topologically Sorted Source Nodes: [mul_13, mul_14, B_4], Original ATen: [aten.mul, aten.add]
# Source node to ATen node mapping:
#   B_4 => add_11
#   mul_13 => mul_15
#   mul_14 => mul_16
# Graph fragment:
#   %mul_15 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%bmm_12, -1.7097828382687081), kwargs = {})
#   %mul_16 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%bmm_13, 0.42323551169305323), kwargs = {})
#   %add_11 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_15, %mul_16), kwargs = {})
triton_poi_fused_add_mul_9 = async_compile.triton('triton_poi_fused_add_mul_9', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.pointwise(
    size_hints={'x': 32}, 
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_add_mul_9', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 2, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_add_mul_9(in_out_ptr0, in_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 27
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = xindex < xnumel
    x0 = xindex
    tmp0 = tl.load(in_out_ptr0 + (x0), xmask).to(tl.float32)
    tmp3 = tl.load(in_ptr0 + (x0), xmask).to(tl.float32)
    tmp1 = -1.7097828382687081
    tmp2 = tmp0 * tmp1
    tmp4 = 0.42323551169305323
    tmp5 = tmp3 * tmp4
    tmp6 = tmp2 + tmp5
    tl.store(in_out_ptr0 + (x0), tmp6, xmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/2c/c2cxgyxkycwunwwhm2godfxonmaypawbfcip3bzastj2fjcz27t7.py
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
#   %mean : [num_users=4] = call_function[target=torch.ops.aten.mean.dim](args = (%pow_3, [-2], True), kwargs = {})
#   %sum_2 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%mean, [-2, -1], True), kwargs = {})
#   %mul_18 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%sum_2, 3), kwargs = {})
#   %sqrt : [num_users=1] = call_function[target=torch.ops.aten.sqrt.default](args = (%mul_18,), kwargs = {})
#   %mul_20 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%mean, 3), kwargs = {})
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
triton_per_fused__to_copy_add_clamp_min_div_lerp_mean_mul_pow_rsqrt_rsub_sqrt_sum_10 = async_compile.triton('triton_per_fused__to_copy_add_clamp_min_div_lerp_mean_mul_pow_rsqrt_rsub_sqrt_sum_10', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 4, 'r': 32},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*fp32', 'in_ptr3': '*fp32', 'out_ptr3': '*bf16', 'out_ptr5': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 7), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_clamp_min_div_lerp_mean_mul_pow_rsqrt_rsub_sqrt_sum_10', 'mutated_arg_names': ['in_ptr3', 'out_ptr5'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 8, 'num_reduction': 2, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_clamp_min_div_lerp_mean_mul_pow_rsqrt_rsub_sqrt_sum_10(in_ptr0, in_ptr1, in_ptr2, in_ptr3, out_ptr3, out_ptr5, xnumel, rnumel, XBLOCK : tl.constexpr):
    xnumel = 3
    rnumel = 32
    RBLOCK: tl.constexpr = 32
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:, None]
    xmask = xindex < xnumel
    rindex = tl.arange(0, RBLOCK)[None, :]
    roffset = 0
    rmask = tl.full([XBLOCK, RBLOCK], True, tl.int1)
    r1 = rindex
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (r1 + 96*x0), xmask, other=0.0).to(tl.float32)
    tmp3 = tl.load(in_ptr1 + (r1 + 96*x0), xmask, other=0.0).to(tl.float32)
    tmp7 = tl.load(in_ptr0 + (32 + r1 + 96*x0), xmask, other=0.0).to(tl.float32)
    tmp9 = tl.load(in_ptr1 + (32 + r1 + 96*x0), xmask, other=0.0).to(tl.float32)
    tmp14 = tl.load(in_ptr0 + (64 + r1 + 96*x0), xmask, other=0.0).to(tl.float32)
    tmp16 = tl.load(in_ptr1 + (64 + r1 + 96*x0), xmask, other=0.0).to(tl.float32)
    tmp28 = tl.load(in_ptr2 + (0))
    tmp29 = tl.broadcast_to(tmp28, [XBLOCK, RBLOCK])
    tmp37 = tl.load(in_ptr3 + (r1 + 32*x0), xmask, other=0.0)
    tmp1 = 2.3465413258596377
    tmp2 = tmp0 * tmp1
    tmp4 = tmp2 + tmp3
    tmp5 = tmp4.to(tl.float32)
    tmp6 = tmp5 * tmp5
    tmp8 = tmp7 * tmp1
    tmp10 = tmp8 + tmp9
    tmp11 = tmp10.to(tl.float32)
    tmp12 = tmp11 * tmp11
    tmp13 = tmp6 + tmp12
    tmp15 = tmp14 * tmp1
    tmp17 = tmp15 + tmp16
    tmp18 = tmp17.to(tl.float32)
    tmp19 = tmp18 * tmp18
    tmp20 = tmp13 + tmp19
    tmp21 = 3.0
    tmp22 = tmp20 / tmp21
    tmp23 = tl.broadcast_to(tmp22, [XBLOCK, RBLOCK])
    tmp25 = tl.where(xmask, tmp23, 0)
    tmp26 = tl.sum(tmp25, 1)[:, None]
    tmp27 = tmp22 * tmp21
    tmp30 = 1.0
    tmp31 = tmp30 - tmp29
    tmp32 = tl_math.abs(tmp31)
    tmp33 = 0.5
    tmp34 = tmp32 >= tmp33
    tmp35 = tmp31 - tmp30
    tmp36 = tl.where(tmp34, tmp35, tmp31)
    tmp38 = tmp22 - tmp37
    tmp39 = tmp36 * tmp38
    tmp40 = tl.where(tmp34, tmp22, tmp37)
    tmp41 = tmp39 + tmp40
    tmp42 = 1e-10
    tmp43 = triton_helpers.maximum(tmp41, tmp42)
    tmp44 = libdevice.rsqrt(tmp43)
    tmp45 = tmp44 * tmp44
    tmp46 = tmp27 * tmp45
    tmp47 = tl.broadcast_to(tmp46, [XBLOCK, RBLOCK])
    tmp49 = tl.where(xmask, tmp47, 0)
    tmp50 = tl.sum(tmp49, 1)[:, None]
    tmp51 = tmp26 * tmp21
    tmp52 = libdevice.sqrt(tmp51)
    tmp53 = libdevice.sqrt(tmp50)
    tmp54 = triton_helpers.maximum(tmp53, tmp42)
    tmp55 = tmp52 / tmp54
    tmp56 = tmp44 * tmp55
    tmp57 = tmp56.to(tl.float32)
    tl.store(out_ptr3 + (r1 + 32*x0), tmp57, xmask)
    tl.store(out_ptr5 + (r1 + 32*x0), tmp41, xmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/lp/clpl53fjiejlxbn6ru4qj534oytvefy3oc7ipu77voiiqu65eljg.py
# Topologically Sorted Source Nodes: [lr, mul_15, X_6, v_norm_sq, v_norm, sub_1, lerp__2, clamp_min, step_size, v_norm_new, clamp_min_1, truediv_1, final_scale, to_8, g_1, mul_22, wd, mul_23, mul_24, mul_21, mask, mul_25, add_11, sub_], Original ATen: [aten._to_copy, aten.mul, aten.add, aten.sqrt, aten.rsub, aten.lerp, aten.clamp_min, aten.rsqrt, aten.div, aten.ge, aten.sub]
# Source node to ATen node mapping:
#   X_6 => add_12
#   add_11 => add_14
#   clamp_min => clamp_min
#   clamp_min_1 => clamp_min_1
#   final_scale => mul_22
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
#   step_size => rsqrt
#   sub_ => sub_8
#   sub_1 => sub_5
#   to_8 => convert_element_type_39
#   truediv_1 => div_1
#   v_norm => sqrt
#   v_norm_new => sqrt_1
#   v_norm_sq => mul_18
#   wd => convert_element_type_41
# Graph fragment:
#   %convert_element_type_40 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%device_put_1, torch.bfloat16), kwargs = {})
#   %mul_17 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%add_10, 2.3465413258596377), kwargs = {})
#   %add_12 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_17, %bmm_14), kwargs = {})
#   %mul_18 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%sum_2, 3), kwargs = {})
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
triton_poi_fused__to_copy_add_clamp_min_div_ge_lerp_mul_rsqrt_rsub_sqrt_sub_11 = async_compile.triton('triton_poi_fused__to_copy_add_clamp_min_div_ge_lerp_mul_rsqrt_rsub_sqrt_sub_11', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.pointwise(
    size_hints={'x': 512}, 
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*fp32', 'in_ptr1': '*fp32', 'in_ptr2': '*bf16', 'in_ptr3': '*bf16', 'in_ptr4': '*bf16', 'in_ptr5': '*fp32', 'out_ptr1': '*fp32', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused__to_copy_add_clamp_min_div_ge_lerp_mul_rsqrt_rsub_sqrt_sub_11', 'mutated_arg_names': ['in_ptr0', 'out_ptr1'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 6, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused__to_copy_add_clamp_min_div_ge_lerp_mul_rsqrt_rsub_sqrt_sub_11(in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, in_ptr5, out_ptr1, xnumel, XBLOCK : tl.constexpr):
    xnumel = 288
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = xindex < xnumel
    x3 = xindex
    x0 = (xindex % 32)
    x2 = xindex // 96
    tmp0 = tl.load(in_ptr0 + (x3), xmask)
    tmp1 = tl.load(in_ptr1 + (0))
    tmp2 = tl.broadcast_to(tmp1, [XBLOCK])
    tmp4 = tl.load(in_ptr2 + (x3), xmask).to(tl.float32)
    tmp7 = tl.load(in_ptr3 + (x3), xmask).to(tl.float32)
    tmp9 = tl.load(in_ptr4 + (x0 + 32*x2), xmask, eviction_policy='evict_last').to(tl.float32)
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
    tl.store(out_ptr1 + (x3), tmp26, xmask)
''', device_str='cuda')


async_compile.wait(globals())
del async_compile

def call(args):
    arg0_1, arg1_1, arg2_1, arg3_1, arg4_1, arg5_1, arg6_1, arg7_1 = args
    args.clear()
    assert_size_stride(arg0_1, (), ())
    assert_size_stride(arg1_1, (3, 3, 32), (96, 32, 1))
    assert_size_stride(arg2_1, (), ())
    assert_size_stride(arg3_1, (), ())
    assert_size_stride(arg4_1, (), ())
    assert_size_stride(arg5_1, (3, 3, 32), (96, 32, 1))
    assert_size_stride(arg6_1, (3, 3, 32), (96, 32, 1))
    assert_size_stride(arg7_1, (3, 1, 32), (32, 32, 1))
    with torch.cuda._DeviceGuard(0):
        torch.cuda.set_device(0)
        buf0 = empty_strided_cuda((), (), torch.float32)
        buf0.copy_(arg2_1, False)
        del arg2_1
        buf1 = empty_strided_cuda((), (), torch.float32)
        buf1.copy_(arg0_1, False)
        del arg0_1
        buf3 = empty_strided_cuda((3, 3, 32), (96, 32, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [g, sub, lerp_, X, norm, mul, add, X_1], Original ATen: [aten.lerp, aten.rsub, aten._to_copy, aten.linalg_vector_norm, aten.mul, aten.add, aten.div]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_div_lerp_linalg_vector_norm_mul_rsub_0.run(buf1, arg5_1, arg6_1, buf3, arg5_1, arg6_1, 3, 96, grid=grid(3), stream=stream0)
        del arg5_1
        del arg6_1
        buf4 = empty_strided_cuda((3, 3, 3), (9, 3, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [A], Original ATen: [aten.bmm]
        extern_kernels.bmm(buf3, reinterpret_tensor(buf3, (3, 32, 3), (96, 1, 32), 0), out=buf4)
        buf5 = empty_strided_cuda((3, 3, 3), (9, 3, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [matmul_1], Original ATen: [aten.bmm]
        extern_kernels.bmm(buf4, buf4, out=buf5)
        buf6 = buf4; del buf4  # reuse
        # Topologically Sorted Source Nodes: [mul_1, mul_2, B], Original ATen: [aten.mul, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_mul_1.run(buf6, buf5, 27, grid=grid(27), stream=stream0)
        buf7 = empty_strided_cuda((3, 3, 32), (96, 32, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [mul_1, mul_2, B, matmul_2], Original ATen: [aten.mul, aten.add, aten.bmm]
        extern_kernels.bmm(buf6, buf3, out=buf7)
        buf8 = empty_strided_cuda((3, 3, 32), (96, 32, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [mul_3, X_2], Original ATen: [aten.mul, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_mul_2.run(buf3, buf7, buf8, 288, grid=grid(288), stream=stream0)
        buf9 = buf6; del buf6  # reuse
        # Topologically Sorted Source Nodes: [mul_3, X_2, A_1], Original ATen: [aten.mul, aten.add, aten.bmm]
        extern_kernels.bmm(buf8, reinterpret_tensor(buf8, (3, 32, 3), (96, 1, 32), 0), out=buf9)
        buf10 = buf5; del buf5  # reuse
        # Topologically Sorted Source Nodes: [matmul_4], Original ATen: [aten.bmm]
        extern_kernels.bmm(buf9, buf9, out=buf10)
        buf11 = buf9; del buf9  # reuse
        # Topologically Sorted Source Nodes: [mul_4, mul_5, B_1], Original ATen: [aten.mul, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_mul_3.run(buf11, buf10, 27, grid=grid(27), stream=stream0)
        buf12 = empty_strided_cuda((3, 3, 32), (96, 32, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [mul_4, mul_5, B_1, matmul_5], Original ATen: [aten.mul, aten.add, aten.bmm]
        extern_kernels.bmm(buf11, buf8, out=buf12)
        buf13 = buf8; del buf8  # reuse
        # Topologically Sorted Source Nodes: [mul_3, X_2, mul_6, X_3], Original ATen: [aten.mul, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_mul_4.run(buf3, buf7, buf12, buf13, 288, grid=grid(288), stream=stream0)
        buf14 = buf11; del buf11  # reuse
        # Topologically Sorted Source Nodes: [mul_3, X_2, mul_6, X_3, A_2], Original ATen: [aten.mul, aten.add, aten.bmm]
        extern_kernels.bmm(buf13, reinterpret_tensor(buf13, (3, 32, 3), (96, 1, 32), 0), out=buf14)
        buf15 = buf10; del buf10  # reuse
        # Topologically Sorted Source Nodes: [matmul_7], Original ATen: [aten.bmm]
        extern_kernels.bmm(buf14, buf14, out=buf15)
        buf16 = buf14; del buf14  # reuse
        # Topologically Sorted Source Nodes: [mul_7, mul_8, B_2], Original ATen: [aten.mul, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_mul_5.run(buf16, buf15, 27, grid=grid(27), stream=stream0)
        buf17 = empty_strided_cuda((3, 3, 32), (96, 32, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [mul_7, mul_8, B_2, matmul_8], Original ATen: [aten.mul, aten.add, aten.bmm]
        extern_kernels.bmm(buf16, buf13, out=buf17)
        buf18 = buf13; del buf13  # reuse
        # Topologically Sorted Source Nodes: [mul_3, X_2, mul_6, X_3, mul_9, X_4], Original ATen: [aten.mul, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_mul_6.run(buf3, buf7, buf12, buf17, buf18, 288, grid=grid(288), stream=stream0)
        buf19 = buf16; del buf16  # reuse
        # Topologically Sorted Source Nodes: [mul_3, X_2, mul_6, X_3, mul_9, X_4, A_3], Original ATen: [aten.mul, aten.add, aten.bmm]
        extern_kernels.bmm(buf18, reinterpret_tensor(buf18, (3, 32, 3), (96, 1, 32), 0), out=buf19)
        buf20 = buf15; del buf15  # reuse
        # Topologically Sorted Source Nodes: [matmul_10], Original ATen: [aten.bmm]
        extern_kernels.bmm(buf19, buf19, out=buf20)
        buf21 = buf19; del buf19  # reuse
        # Topologically Sorted Source Nodes: [mul_10, mul_11, B_3], Original ATen: [aten.mul, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_mul_7.run(buf21, buf20, 27, grid=grid(27), stream=stream0)
        buf22 = empty_strided_cuda((3, 3, 32), (96, 32, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [mul_10, mul_11, B_3, matmul_11], Original ATen: [aten.mul, aten.add, aten.bmm]
        extern_kernels.bmm(buf21, buf18, out=buf22)
        del buf18
        buf23 = buf3; del buf3  # reuse
        # Topologically Sorted Source Nodes: [mul_3, X_2, mul_6, X_3, mul_9, X_4, mul_12, X_5], Original ATen: [aten.mul, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_mul_8.run(buf23, buf7, buf12, buf17, buf22, 288, grid=grid(288), stream=stream0)
        del buf12
        del buf17
        del buf22
        buf24 = buf21; del buf21  # reuse
        # Topologically Sorted Source Nodes: [A_4], Original ATen: [aten.bmm]
        extern_kernels.bmm(buf23, reinterpret_tensor(buf23, (3, 32, 3), (96, 1, 32), 0), out=buf24)
        buf25 = buf20; del buf20  # reuse
        # Topologically Sorted Source Nodes: [matmul_13], Original ATen: [aten.bmm]
        extern_kernels.bmm(buf24, buf24, out=buf25)
        buf26 = buf24; del buf24  # reuse
        # Topologically Sorted Source Nodes: [mul_13, mul_14, B_4], Original ATen: [aten.mul, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_mul_9.run(buf26, buf25, 27, grid=grid(27), stream=stream0)
        del buf25
        buf27 = buf7; del buf7  # reuse
        # Topologically Sorted Source Nodes: [mul_13, mul_14, B_4, matmul_14], Original ATen: [aten.mul, aten.add, aten.bmm]
        extern_kernels.bmm(buf26, buf23, out=buf27)
        del buf26
        buf30 = buf1; del buf1  # reuse
        buf30.copy_(arg4_1, False)
        del arg4_1
        buf32 = empty_strided_cuda((3, 1, 32), (32, 96, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [mul_15, X_6, float_1, square, v_mean, sum_1, v_norm_sq, v_norm, mul_17, sub_1, lerp__2, clamp_min, step_size, square_1, scaled_sq_sum, sum_2, v_norm_new, clamp_min_1, truediv_1, final_scale, to_8], Original ATen: [aten.mul, aten.add, aten._to_copy, aten.pow, aten.mean, aten.sum, aten.sqrt, aten.rsub, aten.lerp, aten.clamp_min, aten.rsqrt, aten.div]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_clamp_min_div_lerp_mean_mul_pow_rsqrt_rsub_sqrt_sum_10.run(buf23, buf27, buf30, arg7_1, buf32, arg7_1, 3, 32, grid=grid(3), stream=stream0)
        del arg7_1
        buf33 = buf30; del buf30  # reuse
        buf33.copy_(arg3_1, False)
        del arg3_1
        # Topologically Sorted Source Nodes: [lr, mul_15, X_6, v_norm_sq, v_norm, sub_1, lerp__2, clamp_min, step_size, v_norm_new, clamp_min_1, truediv_1, final_scale, to_8, g_1, mul_22, wd, mul_23, mul_24, mul_21, mask, mul_25, add_11, sub_], Original ATen: [aten._to_copy, aten.mul, aten.add, aten.sqrt, aten.rsub, aten.lerp, aten.clamp_min, aten.rsqrt, aten.div, aten.ge, aten.sub]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_add_clamp_min_div_ge_lerp_mul_rsqrt_rsub_sqrt_sub_11.run(arg1_1, buf0, buf23, buf27, buf32, buf33, arg1_1, 288, grid=grid(288), stream=stream0)
        del arg1_1
        del buf0
        del buf23
        del buf27
        del buf32
        del buf33
    return ()


def benchmark_compiled_module(times=10, repeat=10):
    from torch._dynamo.testing import rand_strided
    from torch._inductor.utils import print_performance
    arg0_1 = rand_strided((), (), device='cpu', dtype=torch.float32)
    arg1_1 = rand_strided((3, 3, 32), (96, 32, 1), device='cuda:0', dtype=torch.float32)
    arg2_1 = rand_strided((), (), device='cpu', dtype=torch.float32)
    arg3_1 = rand_strided((), (), device='cpu', dtype=torch.float32)
    arg4_1 = rand_strided((), (), device='cpu', dtype=torch.float32)
    arg5_1 = rand_strided((3, 3, 32), (96, 32, 1), device='cuda:0', dtype=torch.float32)
    arg6_1 = rand_strided((3, 3, 32), (96, 32, 1), device='cuda:0', dtype=torch.float32)
    arg7_1 = rand_strided((3, 1, 32), (32, 32, 1), device='cuda:0', dtype=torch.float32)
    fn = lambda: call([arg0_1, arg1_1, arg2_1, arg3_1, arg4_1, arg5_1, arg6_1, arg7_1])
    return print_performance(fn, times=times, repeat=repeat)


if __name__ == "__main__":
    from torch._inductor.wrapper_benchmark import compiled_module_main
    compiled_module_main('None', benchmark_compiled_module)
