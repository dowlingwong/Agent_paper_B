# AOT ID: ['0_forward']
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


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/B2/work/.ar_cache/inductor/x3/cx3jdlwo5snaiyshd7ntktahp3ccdtzrv4oq3xr2xkxpnwtezbqq.py
# Topologically Sorted Source Nodes: [x, x_1, mul, mul_1, x_2, rms_norm_1], Original ATen: [aten.embedding, aten._to_copy, aten.pow, aten.mean, aten.add, aten.rsqrt, aten.mul]
# Source node to ATen node mapping:
#   mul => mul_1
#   mul_1 => mul_2
#   rms_norm_1 => add_2, convert_element_type_2, convert_element_type_3, mean_1, mul_3, pow_2, rsqrt_1
#   x => embedding
#   x_1 => add, convert_element_type, convert_element_type_1, mean, mul, pow_1, rsqrt
#   x_2 => add_1
# Graph fragment:
#   %embedding : [num_users=2] = call_function[target=torch.ops.aten.embedding.default](args = (%primals_4, %primals_1), kwargs = {})
#   %convert_element_type : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%embedding, torch.float32), kwargs = {})
#   %pow_1 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type, 2), kwargs = {})
#   %mean : [num_users=1] = call_function[target=torch.ops.aten.mean.dim](args = (%pow_1, [2], True), kwargs = {})
#   %add : [num_users=1] = call_function[target=torch.ops.aten.add.Scalar](args = (%mean, 0.0078125), kwargs = {})
#   %rsqrt : [num_users=2] = call_function[target=torch.ops.aten.rsqrt.default](args = (%add,), kwargs = {})
#   %mul : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type, %rsqrt), kwargs = {})
#   %convert_element_type_1 : [num_users=5] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul, torch.bfloat16), kwargs = {})
#   %mul_1 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%select, %convert_element_type_1), kwargs = {})
#   %mul_2 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%select_1, %convert_element_type_1), kwargs = {})
#   %add_1 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_1, %mul_2), kwargs = {})
#   %convert_element_type_2 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_1, torch.float32), kwargs = {})
#   %pow_2 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_2, 2), kwargs = {})
#   %mean_1 : [num_users=1] = call_function[target=torch.ops.aten.mean.dim](args = (%pow_2, [2], True), kwargs = {})
#   %add_2 : [num_users=1] = call_function[target=torch.ops.aten.add.Scalar](args = (%mean_1, 0.0078125), kwargs = {})
#   %rsqrt_1 : [num_users=2] = call_function[target=torch.ops.aten.rsqrt.default](args = (%add_2,), kwargs = {})
#   %mul_3 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_2, %rsqrt_1), kwargs = {})
#   %convert_element_type_3 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul_3, torch.bfloat16), kwargs = {})
triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_0 = async_compile.triton('triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_0', '''
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
    triton_meta={'signature': {'in_out_ptr0': '*fp32', 'in_out_ptr1': '*fp32', 'in_ptr0': '*i64', 'in_ptr1': '*bf16', 'in_ptr2': '*fp32', 'in_ptr3': '*fp32', 'out_ptr0': '*bf16', 'out_ptr1': '*bf16', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_0', 'mutated_arg_names': ['in_out_ptr0', 'in_out_ptr1'], 'optimize_mem': False, 'no_x_dim': True, 'num_load': 3, 'num_reduction': 2, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_0(in_out_ptr0, in_out_ptr1, in_ptr0, in_ptr1, in_ptr2, in_ptr3, out_ptr0, out_ptr1, xnumel, rnumel):
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
    x0 = xindex
    r1 = rindex
    tmp0 = tl.load(in_ptr0 + (x0), None, eviction_policy='evict_last')
    tmp17 = tl.load(in_ptr2 + (0))
    tmp18 = tl.broadcast_to(tmp17, [RBLOCK])
    tmp23 = tl.load(in_ptr3 + (0))
    tmp24 = tl.broadcast_to(tmp23, [RBLOCK])
    tmp1 = tl.full([RBLOCK], 8192, tl.int32)
    tmp2 = tmp0 + tmp1
    tmp3 = tmp0 < 0
    tmp4 = tl.where(tmp3, tmp2, tmp0)
    tl.device_assert((0 <= tmp4) & (tmp4 < 8192), "index out of bounds: 0 <= tmp4 < 8192")
    tmp6 = tl.load(in_ptr1 + (r1 + 256*tmp4), None).to(tl.float32)
    tmp7 = tmp6.to(tl.float32)
    tmp8 = tmp7 * tmp7
    tmp9 = tl.broadcast_to(tmp8, [RBLOCK])
    tmp11 = triton_helpers.promote_to_tensor(tl.sum(tmp9, 0))
    tmp12 = 256.0
    tmp13 = tmp11 / tmp12
    tmp14 = 0.0078125
    tmp15 = tmp13 + tmp14
    tmp16 = libdevice.rsqrt(tmp15)
    tmp19 = tmp18.to(tl.float32)
    tmp20 = tmp7 * tmp16
    tmp21 = tmp20.to(tl.float32)
    tmp22 = tmp19 * tmp21
    tmp25 = tmp24.to(tl.float32)
    tmp26 = tmp25 * tmp21
    tmp27 = tmp22 + tmp26
    tmp28 = tmp27.to(tl.float32)
    tmp29 = tmp28 * tmp28
    tmp30 = tl.broadcast_to(tmp29, [RBLOCK])
    tmp32 = triton_helpers.promote_to_tensor(tl.sum(tmp30, 0))
    tmp33 = tmp32 / tmp12
    tmp34 = tmp33 + tmp14
    tmp35 = libdevice.rsqrt(tmp34)
    tmp36 = tmp28 * tmp35
    tmp37 = tmp36.to(tl.float32)
    tl.store(out_ptr0 + (r1 + 256*x0), tmp6, None)
    tl.debug_barrier()
    tl.store(in_out_ptr0 + (x0), tmp16, None)
    tl.debug_barrier()
    tl.store(in_out_ptr1 + (x0), tmp35, None)
    tl.store(out_ptr1 + (r1 + 256*x0), tmp37, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/B2/work/.ar_cache/inductor/yd/cyduuq3za3mvckrkfucuikyd3xhmuebtzydcobu234ktcm3p5efi.py
# Topologically Sorted Source Nodes: [linear], Original ATen: [aten._to_copy, aten.t]
# Source node to ATen node mapping:
#   linear => convert_element_type_4, permute
# Graph fragment:
#   %convert_element_type_4 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%primals_7, torch.bfloat16), kwargs = {})
#   %permute : [num_users=2] = call_function[target=torch.ops.aten.permute.default](args = (%convert_element_type_4, [1, 0]), kwargs = {})
triton_poi_fused__to_copy_t_1 = async_compile.triton('triton_poi_fused__to_copy_t_1', '''
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
    triton_meta={'signature': {'in_ptr0': '*fp32', 'out_ptr0': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused__to_copy_t_1', 'mutated_arg_names': [], 'optimize_mem': False, 'no_x_dim': False, 'num_load': 1, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused__to_copy_t_1(in_ptr0, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 65536
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (x0), None)
    tmp1 = tmp0.to(tl.float32)
    tl.store(out_ptr0 + (x0), tmp1, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/B2/work/.ar_cache/inductor/ul/cul3jq2tomidbjhmnl3x3v4hb67bwikysxshh2bgn34prfoqxunl.py
# Topologically Sorted Source Nodes: [q_1, k_1, q_2, k_2], Original ATen: [aten.cat, aten._to_copy, aten.pow, aten.mean, aten.add, aten.rsqrt, aten.mul]
# Source node to ATen node mapping:
#   k_1 => cat_1
#   k_2 => add_8, convert_element_type_15, convert_element_type_16, mean_3, mul_13, pow_4, rsqrt_3
#   q_1 => cat
#   q_2 => add_7, convert_element_type_13, convert_element_type_14, mean_2, mul_12, pow_3, rsqrt_2
# Graph fragment:
#   %cat : [num_users=2] = call_function[target=torch.ops.aten.cat.default](args = ([%add_3, %add_4], 3), kwargs = {})
#   %cat_1 : [num_users=2] = call_function[target=torch.ops.aten.cat.default](args = ([%add_5, %add_6], 3), kwargs = {})
#   %convert_element_type_13 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%cat, torch.float32), kwargs = {})
#   %pow_3 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_13, 2), kwargs = {})
#   %mean_2 : [num_users=1] = call_function[target=torch.ops.aten.mean.dim](args = (%pow_3, [3], True), kwargs = {})
#   %add_7 : [num_users=1] = call_function[target=torch.ops.aten.add.Scalar](args = (%mean_2, 0.0078125), kwargs = {})
#   %rsqrt_2 : [num_users=2] = call_function[target=torch.ops.aten.rsqrt.default](args = (%add_7,), kwargs = {})
#   %mul_12 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_13, %rsqrt_2), kwargs = {})
#   %convert_element_type_14 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul_12, torch.bfloat16), kwargs = {})
#   %convert_element_type_15 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%cat_1, torch.float32), kwargs = {})
#   %pow_4 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_15, 2), kwargs = {})
#   %mean_3 : [num_users=1] = call_function[target=torch.ops.aten.mean.dim](args = (%pow_4, [3], True), kwargs = {})
#   %add_8 : [num_users=1] = call_function[target=torch.ops.aten.add.Scalar](args = (%mean_3, 0.0078125), kwargs = {})
#   %rsqrt_3 : [num_users=2] = call_function[target=torch.ops.aten.rsqrt.default](args = (%add_8,), kwargs = {})
#   %mul_13 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_15, %rsqrt_3), kwargs = {})
#   %convert_element_type_16 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul_13, torch.bfloat16), kwargs = {})
triton_per_fused__to_copy_add_cat_mean_mul_pow_rsqrt_2 = async_compile.triton('triton_per_fused__to_copy_add_cat_mean_mul_pow_rsqrt_2', '''
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
    triton_meta={'signature': {'in_out_ptr0': '*fp32', 'in_out_ptr1': '*fp32', 'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'in_ptr3': '*bf16', 'out_ptr0': '*bf16', 'out_ptr1': '*bf16', 'out_ptr2': '*bf16', 'out_ptr3': '*bf16', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_cat_mean_mul_pow_rsqrt_2', 'mutated_arg_names': ['in_out_ptr0', 'in_out_ptr1'], 'optimize_mem': False, 'no_x_dim': False, 'num_load': 12, 'num_reduction': 2, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_cat_mean_mul_pow_rsqrt_2(in_out_ptr0, in_out_ptr1, in_ptr0, in_ptr1, in_ptr2, in_ptr3, out_ptr0, out_ptr1, out_ptr2, out_ptr3, xnumel, rnumel, XBLOCK : tl.constexpr):
    xnumel = 65536
    rnumel = 128
    RBLOCK: tl.constexpr = 128
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:, None]
    xmask = tl.full([XBLOCK, RBLOCK], True, tl.int1)
    rindex = tl.arange(0, RBLOCK)[None, :]
    roffset = 0
    rmask = tl.full([XBLOCK, RBLOCK], True, tl.int1)
    r3 = rindex
    x4 = xindex
    x1 = ((xindex // 2) % 2048)
    tmp0 = r3
    tmp1 = tl.full([1, 1], 0, tl.int64)
    tmp2 = tmp0 >= tmp1
    tmp3 = tl.full([1, 1], 64, tl.int64)
    tmp4 = tmp0 < tmp3
    tmp5 = tl.load(in_ptr0 + (128*x4 + (r3)), tmp4, eviction_policy='evict_last', other=0.0).to(tl.float32)
    tmp6 = tl.load(in_ptr1 + (64*x1 + (r3)), tmp4, eviction_policy='evict_last', other=0.0).to(tl.float32)
    tmp7 = tmp5 * tmp6
    tmp8 = tl.load(in_ptr0 + (64 + 128*x4 + (r3)), tmp4, eviction_policy='evict_last', other=0.0).to(tl.float32)
    tmp9 = tl.load(in_ptr2 + (64*x1 + (r3)), tmp4, eviction_policy='evict_last', other=0.0).to(tl.float32)
    tmp10 = tmp8 * tmp9
    tmp11 = tmp7 + tmp10
    tmp12 = tl.full(tmp11.shape, 0.0, tmp11.dtype)
    tmp13 = tl.where(tmp4, tmp11, tmp12)
    tmp14 = tmp0 >= tmp3
    tmp15 = tl.full([1, 1], 128, tl.int64)
    tmp16 = tmp0 < tmp15
    tmp17 = tl.load(in_ptr0 + (128*x4 + ((-64) + r3)), tmp14, eviction_policy='evict_last', other=0.0).to(tl.float32)
    tmp18 = tl.load(in_ptr2 + (64*x1 + ((-64) + r3)), tmp14, eviction_policy='evict_last', other=0.0).to(tl.float32)
    tmp19 = -tmp18
    tmp20 = tmp17 * tmp19
    tmp21 = tl.load(in_ptr0 + (64 + 128*x4 + ((-64) + r3)), tmp14, eviction_policy='evict_last', other=0.0).to(tl.float32)
    tmp22 = tl.load(in_ptr1 + (64*x1 + ((-64) + r3)), tmp14, eviction_policy='evict_last', other=0.0).to(tl.float32)
    tmp23 = tmp21 * tmp22
    tmp24 = tmp20 + tmp23
    tmp25 = tl.full(tmp24.shape, 0.0, tmp24.dtype)
    tmp26 = tl.where(tmp14, tmp24, tmp25)
    tmp27 = tl.where(tmp4, tmp13, tmp26)
    tmp28 = tl.load(in_ptr3 + (128*x4 + (r3)), tmp4, eviction_policy='evict_last', other=0.0).to(tl.float32)
    tmp29 = tmp28 * tmp6
    tmp30 = tl.load(in_ptr3 + (64 + 128*x4 + (r3)), tmp4, eviction_policy='evict_last', other=0.0).to(tl.float32)
    tmp31 = tmp30 * tmp9
    tmp32 = tmp29 + tmp31
    tmp33 = tl.full(tmp32.shape, 0.0, tmp32.dtype)
    tmp34 = tl.where(tmp4, tmp32, tmp33)
    tmp35 = tl.load(in_ptr3 + (128*x4 + ((-64) + r3)), tmp14, eviction_policy='evict_last', other=0.0).to(tl.float32)
    tmp36 = tmp35 * tmp19
    tmp37 = tl.load(in_ptr3 + (64 + 128*x4 + ((-64) + r3)), tmp14, eviction_policy='evict_last', other=0.0).to(tl.float32)
    tmp38 = tmp37 * tmp22
    tmp39 = tmp36 + tmp38
    tmp40 = tl.full(tmp39.shape, 0.0, tmp39.dtype)
    tmp41 = tl.where(tmp14, tmp39, tmp40)
    tmp42 = tl.where(tmp4, tmp34, tmp41)
    tmp43 = tmp27.to(tl.float32)
    tmp44 = tmp43 * tmp43
    tmp45 = tl.broadcast_to(tmp44, [XBLOCK, RBLOCK])
    tmp47 = tl.sum(tmp45, 1)[:, None]
    tmp48 = tmp42.to(tl.float32)
    tmp49 = tmp48 * tmp48
    tmp50 = tl.broadcast_to(tmp49, [XBLOCK, RBLOCK])
    tmp52 = tl.sum(tmp50, 1)[:, None]
    tmp53 = 128.0
    tmp54 = tmp47 / tmp53
    tmp55 = 0.0078125
    tmp56 = tmp54 + tmp55
    tmp57 = libdevice.rsqrt(tmp56)
    tmp58 = tmp52 / tmp53
    tmp59 = tmp58 + tmp55
    tmp60 = libdevice.rsqrt(tmp59)
    tmp61 = tmp43 * tmp57
    tmp62 = tmp61.to(tl.float32)
    tmp63 = tmp48 * tmp60
    tmp64 = tmp63.to(tl.float32)
    tl.store(out_ptr0 + (r3 + 128*x4), tmp27, None)
    tl.store(out_ptr1 + (r3 + 128*x4), tmp42, None)
    tl.debug_barrier()
    tl.store(in_out_ptr0 + (x4), tmp57, None)
    tl.debug_barrier()
    tl.store(in_out_ptr1 + (x4), tmp60, None)
    tl.store(out_ptr2 + (r3 + 128*x4), tmp62, None)
    tl.store(out_ptr3 + (r3 + 128*x4), tmp64, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/B2/work/.ar_cache/inductor/pt/cptxyajuesy2f3q5tjneoziug3gmrn5ccylhrydsq44pookbucyv.py
# Topologically Sorted Source Nodes: [x_1, mul, mul_1, x_2, x_3, rms_norm_4], Original ATen: [aten._to_copy, aten.mul, aten.add, aten.pow, aten.mean, aten.rsqrt]
# Source node to ATen node mapping:
#   mul => mul_1
#   mul_1 => mul_2
#   rms_norm_4 => add_10, convert_element_type_20, convert_element_type_21, mean_4, mul_14, pow_5, rsqrt_4
#   x_1 => convert_element_type, convert_element_type_1, mul
#   x_2 => add_1
#   x_3 => add_9
# Graph fragment:
#   %convert_element_type : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%embedding, torch.float32), kwargs = {})
#   %mul : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type, %rsqrt), kwargs = {})
#   %convert_element_type_1 : [num_users=5] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul, torch.bfloat16), kwargs = {})
#   %mul_1 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%select, %convert_element_type_1), kwargs = {})
#   %mul_2 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%select_1, %convert_element_type_1), kwargs = {})
#   %add_1 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_1, %mul_2), kwargs = {})
#   %add_9 : [num_users=3] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_1, %view_13), kwargs = {})
#   %convert_element_type_20 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_9, torch.float32), kwargs = {})
#   %pow_5 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_20, 2), kwargs = {})
#   %mean_4 : [num_users=1] = call_function[target=torch.ops.aten.mean.dim](args = (%pow_5, [2], True), kwargs = {})
#   %add_10 : [num_users=1] = call_function[target=torch.ops.aten.add.Scalar](args = (%mean_4, 0.0078125), kwargs = {})
#   %rsqrt_4 : [num_users=2] = call_function[target=torch.ops.aten.rsqrt.default](args = (%add_10,), kwargs = {})
#   %mul_14 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_20, %rsqrt_4), kwargs = {})
#   %convert_element_type_21 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul_14, torch.bfloat16), kwargs = {})
triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_3 = async_compile.triton('triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_3', '''
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
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_out_ptr1': '*fp32', 'in_ptr0': '*fp32', 'in_ptr1': '*bf16', 'in_ptr2': '*fp32', 'in_ptr3': '*fp32', 'out_ptr0': '*bf16', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_3', 'mutated_arg_names': ['in_out_ptr0', 'in_out_ptr1'], 'optimize_mem': False, 'no_x_dim': True, 'num_load': 5, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_3(in_out_ptr0, in_out_ptr1, in_ptr0, in_ptr1, in_ptr2, in_ptr3, out_ptr0, xnumel, rnumel):
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
    tmp0 = tl.load(in_ptr0 + (0))
    tmp1 = tl.broadcast_to(tmp0, [RBLOCK])
    tmp3 = tl.load(in_ptr1 + (r1 + 256*x0), None).to(tl.float32)
    tmp5 = tl.load(in_ptr2 + (x0), None, eviction_policy='evict_last')
    tmp9 = tl.load(in_ptr3 + (0))
    tmp10 = tl.broadcast_to(tmp9, [RBLOCK])
    tmp14 = tl.load(in_out_ptr0 + (r1 + 256*x0), None).to(tl.float32)
    tmp2 = tmp1.to(tl.float32)
    tmp4 = tmp3.to(tl.float32)
    tmp6 = tmp4 * tmp5
    tmp7 = tmp6.to(tl.float32)
    tmp8 = tmp2 * tmp7
    tmp11 = tmp10.to(tl.float32)
    tmp12 = tmp11 * tmp7
    tmp13 = tmp8 + tmp12
    tmp15 = tmp13 + tmp14
    tmp16 = tmp15.to(tl.float32)
    tmp17 = tmp16 * tmp16
    tmp18 = tl.broadcast_to(tmp17, [RBLOCK])
    tmp20 = triton_helpers.promote_to_tensor(tl.sum(tmp18, 0))
    tmp21 = 256.0
    tmp22 = tmp20 / tmp21
    tmp23 = 0.0078125
    tmp24 = tmp22 + tmp23
    tmp25 = libdevice.rsqrt(tmp24)
    tmp26 = tmp16 * tmp25
    tmp27 = tmp26.to(tl.float32)
    tl.store(in_out_ptr0 + (r1 + 256*x0), tmp15, None)
    tl.debug_barrier()
    tl.store(in_out_ptr1 + (x0), tmp25, None)
    tl.store(out_ptr0 + (r1 + 256*x0), tmp27, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/B2/work/.ar_cache/inductor/h6/ch6ajrommzeatns7nackchbujhco4ek6s7d2scrsuvcbj6nxz4lu.py
# Topologically Sorted Source Nodes: [x_4], Original ATen: [aten._to_copy, aten.t]
# Source node to ATen node mapping:
#   x_4 => convert_element_type_22, permute_8
# Graph fragment:
#   %convert_element_type_22 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%primals_11, torch.bfloat16), kwargs = {})
#   %permute_8 : [num_users=2] = call_function[target=torch.ops.aten.permute.default](args = (%convert_element_type_22, [1, 0]), kwargs = {})
triton_poi_fused__to_copy_t_4 = async_compile.triton('triton_poi_fused__to_copy_t_4', '''
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
    triton_meta={'signature': {'in_ptr0': '*fp32', 'out_ptr0': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused__to_copy_t_4', 'mutated_arg_names': [], 'optimize_mem': False, 'no_x_dim': False, 'num_load': 1, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused__to_copy_t_4(in_ptr0, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 262144
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (x0), None)
    tmp1 = tmp0.to(tl.float32)
    tl.store(out_ptr0 + (x0), tmp1, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/B2/work/.ar_cache/inductor/a3/ca3bafbblhjjnfjm6jdymx2wvhlktntln3jli7e7wddfvg22vij5.py
# Topologically Sorted Source Nodes: [relu, x_5, x_6], Original ATen: [aten.relu, aten._to_copy, aten.pow]
# Source node to ATen node mapping:
#   relu => relu
#   x_5 => convert_element_type_25, pow_6
#   x_6 => convert_element_type_27
# Graph fragment:
#   %relu : [num_users=1] = call_function[target=torch.ops.aten.relu.default](args = (%view_15,), kwargs = {})
#   %convert_element_type_25 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%relu, torch.float32), kwargs = {})
#   %pow_6 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_25, 2), kwargs = {})
#   %convert_element_type_27 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%pow_6, torch.bfloat16), kwargs = {})
triton_poi_fused__to_copy_pow_relu_5 = async_compile.triton('triton_poi_fused__to_copy_pow_relu_5', '''
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
    triton_meta={'signature': {'in_ptr0': '*bf16', 'out_ptr0': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused__to_copy_pow_relu_5', 'mutated_arg_names': [], 'optimize_mem': False, 'no_x_dim': False, 'num_load': 1, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused__to_copy_pow_relu_5(in_ptr0, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 33554432
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (x0), None).to(tl.float32)
    tmp1 = tl.full([1], 0, tl.int32)
    tmp2 = triton_helpers.maximum(tmp1, tmp0)
    tmp3 = tmp2.to(tl.float32)
    tmp4 = tmp3 * tmp3
    tmp5 = tmp4.to(tl.float32)
    tl.store(out_ptr0 + (x0), tmp5, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/B2/work/.ar_cache/inductor/x4/cx4t3pphwmd3ns74vptwfm4jb3c5xximmz32haikuidhnhb2xn3q.py
# Topologically Sorted Source Nodes: [x_1, x_7, mul_10, mul_11, x_8, rms_norm_5], Original ATen: [aten._to_copy, aten.mul, aten.add, aten.pow, aten.mean, aten.rsqrt]
# Source node to ATen node mapping:
#   mul_10 => mul_15
#   mul_11 => mul_16
#   rms_norm_5 => add_13, convert_element_type_30, convert_element_type_31, mean_5, mul_17, pow_7, rsqrt_5
#   x_1 => convert_element_type, convert_element_type_1, mul
#   x_7 => add_11
#   x_8 => add_12
# Graph fragment:
#   %convert_element_type : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%embedding, torch.float32), kwargs = {})
#   %mul : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type, %rsqrt), kwargs = {})
#   %convert_element_type_1 : [num_users=5] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul, torch.bfloat16), kwargs = {})
#   %add_11 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_9, %view_17), kwargs = {})
#   %mul_15 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%select_2, %add_11), kwargs = {})
#   %mul_16 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%select_3, %convert_element_type_1), kwargs = {})
#   %add_12 : [num_users=3] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_15, %mul_16), kwargs = {})
#   %convert_element_type_30 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_12, torch.float32), kwargs = {})
#   %pow_7 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_30, 2), kwargs = {})
#   %mean_5 : [num_users=1] = call_function[target=torch.ops.aten.mean.dim](args = (%pow_7, [2], True), kwargs = {})
#   %add_13 : [num_users=1] = call_function[target=torch.ops.aten.add.Scalar](args = (%mean_5, 0.0078125), kwargs = {})
#   %rsqrt_5 : [num_users=2] = call_function[target=torch.ops.aten.rsqrt.default](args = (%add_13,), kwargs = {})
#   %mul_17 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_30, %rsqrt_5), kwargs = {})
#   %convert_element_type_31 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul_17, torch.bfloat16), kwargs = {})
triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_6 = async_compile.triton('triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_6', '''
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
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_out_ptr1': '*fp32', 'in_ptr0': '*bf16', 'in_ptr1': '*fp32', 'in_ptr2': '*fp32', 'in_ptr3': '*bf16', 'in_ptr4': '*fp32', 'out_ptr0': '*bf16', 'out_ptr1': '*bf16', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_6', 'mutated_arg_names': ['in_out_ptr0', 'in_out_ptr1'], 'optimize_mem': False, 'no_x_dim': True, 'num_load': 6, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_6(in_out_ptr0, in_out_ptr1, in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, out_ptr0, out_ptr1, xnumel, rnumel):
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
    tmp1 = tl.load(in_out_ptr0 + (r1 + 256*x0), None).to(tl.float32)
    tmp3 = tl.load(in_ptr1 + (1))
    tmp4 = tl.broadcast_to(tmp3, [RBLOCK])
    tmp7 = tl.load(in_ptr2 + (1))
    tmp8 = tl.broadcast_to(tmp7, [RBLOCK])
    tmp10 = tl.load(in_ptr3 + (r1 + 256*x0), None).to(tl.float32)
    tmp12 = tl.load(in_ptr4 + (x0), None, eviction_policy='evict_last')
    tmp2 = tmp0 + tmp1
    tmp5 = tmp4.to(tl.float32)
    tmp6 = tmp5 * tmp2
    tmp9 = tmp8.to(tl.float32)
    tmp11 = tmp10.to(tl.float32)
    tmp13 = tmp11 * tmp12
    tmp14 = tmp13.to(tl.float32)
    tmp15 = tmp9 * tmp14
    tmp16 = tmp6 + tmp15
    tmp17 = tmp16.to(tl.float32)
    tmp18 = tmp17 * tmp17
    tmp19 = tl.broadcast_to(tmp18, [RBLOCK])
    tmp21 = triton_helpers.promote_to_tensor(tl.sum(tmp19, 0))
    tmp22 = 256.0
    tmp23 = tmp21 / tmp22
    tmp24 = 0.0078125
    tmp25 = tmp23 + tmp24
    tmp26 = libdevice.rsqrt(tmp25)
    tmp27 = tmp17 * tmp26
    tmp28 = tmp27.to(tl.float32)
    tl.store(in_out_ptr0 + (r1 + 256*x0), tmp2, None)
    tl.store(out_ptr0 + (r1 + 256*x0), tmp16, None)
    tl.debug_barrier()
    tl.store(in_out_ptr1 + (x0), tmp26, None)
    tl.store(out_ptr1 + (r1 + 256*x0), tmp28, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/B2/work/.ar_cache/inductor/bd/cbdc6am646dpgii6l75647y4v2aibbmwck5qzh3bwa47xkbpjfmv.py
# Topologically Sorted Source Nodes: [linear_9], Original ATen: [aten._to_copy, aten.t]
# Source node to ATen node mapping:
#   linear_9 => convert_element_type_41, permute_13
# Graph fragment:
#   %convert_element_type_41 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%primals_17, torch.bfloat16), kwargs = {})
#   %permute_13 : [num_users=2] = call_function[target=torch.ops.aten.permute.default](args = (%convert_element_type_41, [1, 0]), kwargs = {})
triton_poi_fused__to_copy_t_7 = async_compile.triton('triton_poi_fused__to_copy_t_7', '''
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
    triton_meta={'signature': {'in_ptr0': '*fp32', 'out_ptr0': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused__to_copy_t_7', 'mutated_arg_names': [], 'optimize_mem': False, 'no_x_dim': False, 'num_load': 1, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused__to_copy_t_7(in_ptr0, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 64
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = xindex < xnumel
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (x0), xmask)
    tmp1 = tmp0.to(tl.float32)
    tl.store(out_ptr0 + (x0), tmp1, xmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/B2/work/.ar_cache/inductor/hx/chxjfl6wh77uo3k46p55mw7tfbubjebfsnbzekabukkkkwizvo23.py
# Topologically Sorted Source Nodes: [ve, mul_13, v_4], Original ATen: [aten.embedding, aten.mul, aten.add]
# Source node to ATen node mapping:
#   mul_13 => mul_19
#   v_4 => add_14
#   ve => embedding_1
# Graph fragment:
#   %embedding_1 : [num_users=2] = call_function[target=torch.ops.aten.embedding.default](args = (%primals_13, %primals_1), kwargs = {})
#   %mul_19 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%unsqueeze_2, %view_27), kwargs = {})
#   %add_14 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%view_26, %mul_19), kwargs = {})
triton_poi_fused_add_embedding_mul_8 = async_compile.triton('triton_poi_fused_add_embedding_mul_8', '''
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
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*i64', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'out_ptr0': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_add_embedding_mul_8', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': False, 'no_x_dim': False, 'num_load': 3, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_add_embedding_mul_8(in_out_ptr0, in_ptr0, in_ptr1, in_ptr2, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 8388608
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x1 = xindex // 256
    x0 = (xindex % 256)
    x4 = xindex
    x3 = xindex // 128
    tmp0 = tl.load(in_ptr0 + (x1), None, eviction_policy='evict_last')
    tmp7 = tl.load(in_out_ptr0 + (x4), None).to(tl.float32)
    tmp8 = tl.load(in_ptr2 + (x3), None, eviction_policy='evict_last').to(tl.float32)
    tmp1 = tl.full([XBLOCK], 8192, tl.int32)
    tmp2 = tmp0 + tmp1
    tmp3 = tmp0 < 0
    tmp4 = tl.where(tmp3, tmp2, tmp0)
    tl.device_assert((0 <= tmp4) & (tmp4 < 8192), "index out of bounds: 0 <= tmp4 < 8192")
    tmp6 = tl.load(in_ptr1 + (x0 + 256*tmp4), None).to(tl.float32)
    tmp9 = tl.sigmoid(tmp8)
    tmp10 = 2.0
    tmp11 = tmp9 * tmp10
    tmp12 = tmp11 * tmp6
    tmp13 = tmp7 + tmp12
    tl.store(out_ptr0 + (x4), tmp6, None)
    tl.store(in_out_ptr0 + (x4), tmp13, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/B2/work/.ar_cache/inductor/im/cimoix6bjdchjqxnsmfg65cqzrb7cs52qjqoe44bwftmqx4zv25e.py
# Topologically Sorted Source Nodes: [x_9, rms_norm_8], Original ATen: [aten.add, aten._to_copy, aten.pow, aten.mean, aten.rsqrt, aten.mul]
# Source node to ATen node mapping:
#   rms_norm_8 => add_22, convert_element_type_51, convert_element_type_52, mean_8, mul_30, pow_10, rsqrt_8
#   x_9 => add_21
# Graph fragment:
#   %add_21 : [num_users=3] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_12, %view_34), kwargs = {})
#   %convert_element_type_51 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_21, torch.float32), kwargs = {})
#   %pow_10 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_51, 2), kwargs = {})
#   %mean_8 : [num_users=1] = call_function[target=torch.ops.aten.mean.dim](args = (%pow_10, [2], True), kwargs = {})
#   %add_22 : [num_users=1] = call_function[target=torch.ops.aten.add.Scalar](args = (%mean_8, 0.0078125), kwargs = {})
#   %rsqrt_8 : [num_users=2] = call_function[target=torch.ops.aten.rsqrt.default](args = (%add_22,), kwargs = {})
#   %mul_30 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_51, %rsqrt_8), kwargs = {})
#   %convert_element_type_52 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul_30, torch.bfloat16), kwargs = {})
triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_9 = async_compile.triton('triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_9', '''
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
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_out_ptr1': '*fp32', 'in_ptr0': '*bf16', 'out_ptr0': '*bf16', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_9', 'mutated_arg_names': ['in_out_ptr0', 'in_out_ptr1'], 'optimize_mem': False, 'no_x_dim': True, 'num_load': 2, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_9(in_out_ptr0, in_out_ptr1, in_ptr0, out_ptr0, xnumel, rnumel):
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
    tmp1 = tl.load(in_out_ptr0 + (r1 + 256*x0), None).to(tl.float32)
    tmp2 = tmp0 + tmp1
    tmp3 = tmp2.to(tl.float32)
    tmp4 = tmp3 * tmp3
    tmp5 = tl.broadcast_to(tmp4, [RBLOCK])
    tmp7 = triton_helpers.promote_to_tensor(tl.sum(tmp5, 0))
    tmp8 = 256.0
    tmp9 = tmp7 / tmp8
    tmp10 = 0.0078125
    tmp11 = tmp9 + tmp10
    tmp12 = libdevice.rsqrt(tmp11)
    tmp13 = tmp3 * tmp12
    tmp14 = tmp13.to(tl.float32)
    tl.store(in_out_ptr0 + (r1 + 256*x0), tmp2, None)
    tl.debug_barrier()
    tl.store(in_out_ptr1 + (x0), tmp12, None)
    tl.store(out_ptr0 + (r1 + 256*x0), tmp14, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/B2/work/.ar_cache/inductor/4k/c4kn322gm3vuluanty3grna3oekmf3lkk7ynqsxgc53c3sxq73hp.py
# Topologically Sorted Source Nodes: [x_1, x_13, mul_22, mul_23, x_14, rms_norm_9], Original ATen: [aten._to_copy, aten.mul, aten.add, aten.pow, aten.mean, aten.rsqrt]
# Source node to ATen node mapping:
#   mul_22 => mul_31
#   mul_23 => mul_32
#   rms_norm_9 => add_25, convert_element_type_61, convert_element_type_62, mean_9, mul_33, pow_12, rsqrt_9
#   x_1 => convert_element_type, convert_element_type_1, mul
#   x_13 => add_23
#   x_14 => add_24
# Graph fragment:
#   %convert_element_type : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%embedding, torch.float32), kwargs = {})
#   %mul : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type, %rsqrt), kwargs = {})
#   %convert_element_type_1 : [num_users=5] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul, torch.bfloat16), kwargs = {})
#   %add_23 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_21, %view_38), kwargs = {})
#   %mul_31 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%select_4, %add_23), kwargs = {})
#   %mul_32 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%select_5, %convert_element_type_1), kwargs = {})
#   %add_24 : [num_users=3] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_31, %mul_32), kwargs = {})
#   %convert_element_type_61 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_24, torch.float32), kwargs = {})
#   %pow_12 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_61, 2), kwargs = {})
#   %mean_9 : [num_users=1] = call_function[target=torch.ops.aten.mean.dim](args = (%pow_12, [2], True), kwargs = {})
#   %add_25 : [num_users=1] = call_function[target=torch.ops.aten.add.Scalar](args = (%mean_9, 0.0078125), kwargs = {})
#   %rsqrt_9 : [num_users=2] = call_function[target=torch.ops.aten.rsqrt.default](args = (%add_25,), kwargs = {})
#   %mul_33 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_61, %rsqrt_9), kwargs = {})
#   %convert_element_type_62 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul_33, torch.bfloat16), kwargs = {})
triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_10 = async_compile.triton('triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_10', '''
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
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_out_ptr1': '*fp32', 'in_ptr0': '*bf16', 'in_ptr1': '*fp32', 'in_ptr2': '*fp32', 'in_ptr3': '*bf16', 'in_ptr4': '*fp32', 'out_ptr0': '*bf16', 'out_ptr1': '*bf16', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_10', 'mutated_arg_names': ['in_out_ptr0', 'in_out_ptr1'], 'optimize_mem': False, 'no_x_dim': True, 'num_load': 6, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_10(in_out_ptr0, in_out_ptr1, in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, out_ptr0, out_ptr1, xnumel, rnumel):
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
    tmp1 = tl.load(in_out_ptr0 + (r1 + 256*x0), None).to(tl.float32)
    tmp3 = tl.load(in_ptr1 + (2))
    tmp4 = tl.broadcast_to(tmp3, [RBLOCK])
    tmp7 = tl.load(in_ptr2 + (2))
    tmp8 = tl.broadcast_to(tmp7, [RBLOCK])
    tmp10 = tl.load(in_ptr3 + (r1 + 256*x0), None).to(tl.float32)
    tmp12 = tl.load(in_ptr4 + (x0), None, eviction_policy='evict_last')
    tmp2 = tmp0 + tmp1
    tmp5 = tmp4.to(tl.float32)
    tmp6 = tmp5 * tmp2
    tmp9 = tmp8.to(tl.float32)
    tmp11 = tmp10.to(tl.float32)
    tmp13 = tmp11 * tmp12
    tmp14 = tmp13.to(tl.float32)
    tmp15 = tmp9 * tmp14
    tmp16 = tmp6 + tmp15
    tmp17 = tmp16.to(tl.float32)
    tmp18 = tmp17 * tmp17
    tmp19 = tl.broadcast_to(tmp18, [RBLOCK])
    tmp21 = triton_helpers.promote_to_tensor(tl.sum(tmp19, 0))
    tmp22 = 256.0
    tmp23 = tmp21 / tmp22
    tmp24 = 0.0078125
    tmp25 = tmp23 + tmp24
    tmp26 = libdevice.rsqrt(tmp25)
    tmp27 = tmp17 * tmp26
    tmp28 = tmp27.to(tl.float32)
    tl.store(in_out_ptr0 + (r1 + 256*x0), tmp2, None)
    tl.store(out_ptr0 + (r1 + 256*x0), tmp16, None)
    tl.debug_barrier()
    tl.store(in_out_ptr1 + (x0), tmp26, None)
    tl.store(out_ptr1 + (r1 + 256*x0), tmp28, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/B2/work/.ar_cache/inductor/bj/cbjga3i732kmyrg6qodeaq4k4miny46vudalr7a6c4yusd5uvb7e.py
# Topologically Sorted Source Nodes: [x_1, x_19, mul_32, mul_33, x_20, rms_norm_13], Original ATen: [aten._to_copy, aten.mul, aten.add, aten.pow, aten.mean, aten.rsqrt]
# Source node to ATen node mapping:
#   mul_32 => mul_45
#   mul_33 => mul_46
#   rms_norm_13 => add_36, convert_element_type_89, convert_element_type_90, mean_13, mul_47, pow_17, rsqrt_13
#   x_1 => convert_element_type, convert_element_type_1, mul
#   x_19 => add_34
#   x_20 => add_35
# Graph fragment:
#   %convert_element_type : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%embedding, torch.float32), kwargs = {})
#   %mul : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type, %rsqrt), kwargs = {})
#   %convert_element_type_1 : [num_users=5] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul, torch.bfloat16), kwargs = {})
#   %add_34 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_32, %view_56), kwargs = {})
#   %mul_45 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%select_6, %add_34), kwargs = {})
#   %mul_46 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%select_7, %convert_element_type_1), kwargs = {})
#   %add_35 : [num_users=3] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_45, %mul_46), kwargs = {})
#   %convert_element_type_89 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_35, torch.float32), kwargs = {})
#   %pow_17 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_89, 2), kwargs = {})
#   %mean_13 : [num_users=1] = call_function[target=torch.ops.aten.mean.dim](args = (%pow_17, [2], True), kwargs = {})
#   %add_36 : [num_users=1] = call_function[target=torch.ops.aten.add.Scalar](args = (%mean_13, 0.0078125), kwargs = {})
#   %rsqrt_13 : [num_users=2] = call_function[target=torch.ops.aten.rsqrt.default](args = (%add_36,), kwargs = {})
#   %mul_47 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_89, %rsqrt_13), kwargs = {})
#   %convert_element_type_90 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul_47, torch.bfloat16), kwargs = {})
triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_11 = async_compile.triton('triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_11', '''
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
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_out_ptr1': '*fp32', 'in_ptr0': '*bf16', 'in_ptr1': '*fp32', 'in_ptr2': '*fp32', 'in_ptr3': '*bf16', 'in_ptr4': '*fp32', 'out_ptr0': '*bf16', 'out_ptr1': '*bf16', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_11', 'mutated_arg_names': ['in_out_ptr0', 'in_out_ptr1'], 'optimize_mem': False, 'no_x_dim': True, 'num_load': 6, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_11(in_out_ptr0, in_out_ptr1, in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, out_ptr0, out_ptr1, xnumel, rnumel):
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
    tmp1 = tl.load(in_out_ptr0 + (r1 + 256*x0), None).to(tl.float32)
    tmp3 = tl.load(in_ptr1 + (3))
    tmp4 = tl.broadcast_to(tmp3, [RBLOCK])
    tmp7 = tl.load(in_ptr2 + (3))
    tmp8 = tl.broadcast_to(tmp7, [RBLOCK])
    tmp10 = tl.load(in_ptr3 + (r1 + 256*x0), None).to(tl.float32)
    tmp12 = tl.load(in_ptr4 + (x0), None, eviction_policy='evict_last')
    tmp2 = tmp0 + tmp1
    tmp5 = tmp4.to(tl.float32)
    tmp6 = tmp5 * tmp2
    tmp9 = tmp8.to(tl.float32)
    tmp11 = tmp10.to(tl.float32)
    tmp13 = tmp11 * tmp12
    tmp14 = tmp13.to(tl.float32)
    tmp15 = tmp9 * tmp14
    tmp16 = tmp6 + tmp15
    tmp17 = tmp16.to(tl.float32)
    tmp18 = tmp17 * tmp17
    tmp19 = tl.broadcast_to(tmp18, [RBLOCK])
    tmp21 = triton_helpers.promote_to_tensor(tl.sum(tmp19, 0))
    tmp22 = 256.0
    tmp23 = tmp21 / tmp22
    tmp24 = 0.0078125
    tmp25 = tmp23 + tmp24
    tmp26 = libdevice.rsqrt(tmp25)
    tmp27 = tmp17 * tmp26
    tmp28 = tmp27.to(tl.float32)
    tl.store(in_out_ptr0 + (r1 + 256*x0), tmp2, None)
    tl.store(out_ptr0 + (r1 + 256*x0), tmp16, None)
    tl.debug_barrier()
    tl.store(in_out_ptr1 + (x0), tmp26, None)
    tl.store(out_ptr1 + (r1 + 256*x0), tmp28, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/B2/work/.ar_cache/inductor/jg/cjg2gym3eeg3bn54lctmc2ifsno2n4sykrcl4zbjn2viktbfs5i7.py
# Topologically Sorted Source Nodes: [logits], Original ATen: [aten._to_copy, aten.t]
# Source node to ATen node mapping:
#   logits => convert_element_type_122, permute_42
# Graph fragment:
#   %convert_element_type_122 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%primals_35, torch.bfloat16), kwargs = {})
#   %permute_42 : [num_users=2] = call_function[target=torch.ops.aten.permute.default](args = (%convert_element_type_122, [1, 0]), kwargs = {})
triton_poi_fused__to_copy_t_12 = async_compile.triton('triton_poi_fused__to_copy_t_12', '''
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
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused__to_copy_t_12', 'mutated_arg_names': [], 'optimize_mem': False, 'no_x_dim': False, 'num_load': 1, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused__to_copy_t_12(in_ptr0, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 2097152
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (x0), None)
    tmp1 = tmp0.to(tl.float32)
    tl.store(out_ptr0 + (x0), tmp1, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/B2/work/.ar_cache/inductor/pl/cplqtg6klq33e252mk3famxfjwgzyshzyj43dhuai5iutakkwslw.py
# Topologically Sorted Source Nodes: [loss], Original ATen: [aten._log_softmax]
# Source node to ATen node mapping:
#   loss => amax, exp, log, sub, sum_1
# Graph fragment:
#   %amax : [num_users=2] = call_function[target=torch.ops.aten.amax.default](args = (%view_80, [1], True), kwargs = {})
#   %sub : [num_users=2] = call_function[target=torch.ops.aten.sub.Tensor](args = (%view_80, %amax), kwargs = {})
#   %exp : [num_users=1] = call_function[target=torch.ops.aten.exp.default](args = (%sub,), kwargs = {})
#   %sum_1 : [num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%exp, [1], True), kwargs = {})
#   %log : [num_users=2] = call_function[target=torch.ops.aten.log.default](args = (%sum_1,), kwargs = {})
triton_red_fused__log_softmax_13 = async_compile.triton('triton_red_fused__log_softmax_13', '''
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
    triton_meta={'signature': {'in_out_ptr0': '*fp32', 'in_ptr0': '*bf16', 'out_ptr0': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_red_fused__log_softmax_13', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': False, 'no_x_dim': False, 'num_load': 2, 'num_reduction': 2, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_red_fused__log_softmax_13(in_out_ptr0, in_ptr0, out_ptr0, xnumel, rnumel, XBLOCK : tl.constexpr, RBLOCK : tl.constexpr):
    xnumel = 32768
    rnumel = 8192
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:, None]
    xmask = tl.full([XBLOCK, RBLOCK], True, tl.int1)
    rbase = tl.arange(0, RBLOCK)[None, :]
    x0 = xindex
    _tmp8 = tl.full([XBLOCK, RBLOCK], float("-inf"), tl.float32)
    for roffset in range(0, rnumel, RBLOCK):
        rindex = roffset + rbase
        rmask = rindex < rnumel
        r1 = rindex
        tmp0 = tl.load(in_ptr0 + (r1 + 8192*x0), rmask, eviction_policy='evict_last', other=0.0).to(tl.float32)
        tmp1 = tmp0.to(tl.float32)
        tmp2 = 0.06666666666666667
        tmp3 = tmp1 * tmp2
        tmp4 = libdevice.tanh(tmp3)
        tmp5 = 15.0
        tmp6 = tmp4 * tmp5
        tmp7 = tl.broadcast_to(tmp6, [XBLOCK, RBLOCK])
        tmp9 = triton_helpers.maximum(_tmp8, tmp7)
        _tmp8 = tl.where(rmask, tmp9, _tmp8)
    tmp8 = triton_helpers.max2(_tmp8, 1)[:, None]
    tl.store(out_ptr0 + (x0), tmp8, None)
    _tmp20 = tl.full([XBLOCK, RBLOCK], 0, tl.float32)
    for roffset in range(0, rnumel, RBLOCK):
        rindex = roffset + rbase
        rmask = rindex < rnumel
        r1 = rindex
        tmp10 = tl.load(in_ptr0 + (r1 + 8192*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp11 = tmp10.to(tl.float32)
        tmp12 = 0.06666666666666667
        tmp13 = tmp11 * tmp12
        tmp14 = libdevice.tanh(tmp13)
        tmp15 = 15.0
        tmp16 = tmp14 * tmp15
        tmp17 = tmp16 - tmp8
        tmp18 = tl_math.exp(tmp17)
        tmp19 = tl.broadcast_to(tmp18, [XBLOCK, RBLOCK])
        tmp21 = _tmp20 + tmp19
        _tmp20 = tl.where(rmask, tmp21, _tmp20)
    tmp20 = tl.sum(_tmp20, 1)[:, None]
    tmp22 = tl_math.log(tmp20)
    tl.debug_barrier()
    tl.store(in_out_ptr0 + (x0), tmp22, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/B2/work/.ar_cache/inductor/yv/cyvlntihg3j3bgrixjwee2mn2mzj7p2hhbvxm6ernahbah4befb2.py
# Topologically Sorted Source Nodes: [loss], Original ATen: [aten.nll_loss_forward]
# Source node to ATen node mapping:
#   loss => full_default_1, ne, neg_8, sum_2, sum_3, where_1
# Graph fragment:
#   %ne : [num_users=3] = call_function[target=torch.ops.aten.ne.Scalar](args = (%view_81, -1), kwargs = {})
#   %neg_8 : [num_users=1] = call_function[target=torch.ops.aten.neg.default](args = (%squeeze,), kwargs = {})
#   %full_default_1 : [num_users=1] = call_function[target=torch.ops.aten.full.default](args = ([], 0.0), kwargs = {dtype: torch.float32, layout: torch.strided, device: cuda:0, pin_memory: False})
#   %where_1 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%ne, %neg_8, %full_default_1), kwargs = {})
#   %sum_2 : [num_users=1] = call_function[target=torch.ops.aten.sum.default](args = (%ne,), kwargs = {})
#   %sum_3 : [num_users=1] = call_function[target=torch.ops.aten.sum.default](args = (%where_1,), kwargs = {})
triton_red_fused_nll_loss_forward_14 = async_compile.triton('triton_red_fused_nll_loss_forward_14', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.reduction(
    size_hints={'x': 4, 'r': 8192},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*i64', 'in_ptr1': '*bf16', 'in_ptr2': '*fp32', 'in_ptr3': '*fp32', 'out_ptr0': '*i64', 'out_ptr1': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 7), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_red_fused_nll_loss_forward_14', 'mutated_arg_names': [], 'optimize_mem': False, 'no_x_dim': False, 'num_load': 3, 'num_reduction': 2, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_red_fused_nll_loss_forward_14(in_ptr0, in_ptr1, in_ptr2, in_ptr3, out_ptr0, out_ptr1, xnumel, rnumel, XBLOCK : tl.constexpr, RBLOCK : tl.constexpr):
    xnumel = 4
    rnumel = 8192
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:, None]
    xmask = xindex < xnumel
    rbase = tl.arange(0, RBLOCK)[None, :]
    x0 = xindex
    _tmp5 = tl.full([XBLOCK, RBLOCK], 0, tl.int64)
    _tmp29 = tl.full([XBLOCK, RBLOCK], 0, tl.float32)
    for roffset in range(0, rnumel, RBLOCK):
        rindex = roffset + rbase
        rmask = rindex < rnumel
        r1 = rindex
        tmp0 = tl.load(in_ptr0 + (r1 + 8192*x0), rmask & xmask, eviction_policy='evict_first', other=0.0)
        tmp21 = tl.load(in_ptr2 + (r1 + 8192*x0), rmask & xmask, eviction_policy='evict_first', other=0.0)
        tmp23 = tl.load(in_ptr3 + (r1 + 8192*x0), rmask & xmask, eviction_policy='evict_first', other=0.0)
        tmp1 = tl.full([1, 1], -1, tl.int64)
        tmp2 = tmp0 != tmp1
        tmp3 = tmp2.to(tl.int64)
        tmp4 = tl.broadcast_to(tmp3, [XBLOCK, RBLOCK])
        tmp6 = _tmp5 + tmp4
        _tmp5 = tl.where(rmask & xmask, tmp6, _tmp5)
        tmp7 = tl.full([1, 1], 0, tl.int64)
        tmp8 = tl.where(tmp2, tmp0, tmp7)
        tmp9 = tl.full([XBLOCK, RBLOCK], 8192, tl.int32)
        tmp10 = tmp8 + tmp9
        tmp11 = tmp8 < 0
        tmp12 = tl.where(tmp11, tmp10, tmp8)
        tl.device_assert(((0 <= tmp12) & (tmp12 < 8192)) | ~(rmask & xmask), "index out of bounds: 0 <= tmp12 < 8192")
        tmp14 = tl.load(in_ptr1 + (tmp12 + 8192*r1 + 67108864*x0), rmask & xmask, eviction_policy='evict_last', other=0.0).to(tl.float32)
        tmp15 = tmp14.to(tl.float32)
        tmp16 = 0.06666666666666667
        tmp17 = tmp15 * tmp16
        tmp18 = libdevice.tanh(tmp17)
        tmp19 = 15.0
        tmp20 = tmp18 * tmp19
        tmp22 = tmp20 - tmp21
        tmp24 = tmp22 - tmp23
        tmp25 = -tmp24
        tmp26 = 0.0
        tmp27 = tl.where(tmp2, tmp25, tmp26)
        tmp28 = tl.broadcast_to(tmp27, [XBLOCK, RBLOCK])
        tmp30 = _tmp29 + tmp28
        _tmp29 = tl.where(rmask & xmask, tmp30, _tmp29)
    tmp5 = tl.sum(_tmp5, 1)[:, None]
    tmp29 = tl.sum(_tmp29, 1)[:, None]
    tl.store(out_ptr0 + (x0), tmp5, xmask)
    tl.store(out_ptr1 + (x0), tmp29, xmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/B2/work/.ar_cache/inductor/2f/c2f2zostfnuafnhanzxyy3sjp6i57645zwd234pz5jz7iqjo7njl.py
# Topologically Sorted Source Nodes: [loss], Original ATen: [aten.nll_loss_forward]
# Source node to ATen node mapping:
#   loss => convert_element_type_126, div_1, full_default_1, ne, neg_8, sum_2, sum_3, where_1
# Graph fragment:
#   %ne : [num_users=3] = call_function[target=torch.ops.aten.ne.Scalar](args = (%view_81, -1), kwargs = {})
#   %neg_8 : [num_users=1] = call_function[target=torch.ops.aten.neg.default](args = (%squeeze,), kwargs = {})
#   %full_default_1 : [num_users=1] = call_function[target=torch.ops.aten.full.default](args = ([], 0.0), kwargs = {dtype: torch.float32, layout: torch.strided, device: cuda:0, pin_memory: False})
#   %where_1 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%ne, %neg_8, %full_default_1), kwargs = {})
#   %sum_2 : [num_users=1] = call_function[target=torch.ops.aten.sum.default](args = (%ne,), kwargs = {})
#   %convert_element_type_126 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%sum_2, torch.float32), kwargs = {})
#   %sum_3 : [num_users=1] = call_function[target=torch.ops.aten.sum.default](args = (%where_1,), kwargs = {})
#   %div_1 : [num_users=1] = call_function[target=torch.ops.aten.div.Tensor](args = (%sum_3, %convert_element_type_126), kwargs = {})
triton_per_fused_nll_loss_forward_15 = async_compile.triton('triton_per_fused_nll_loss_forward_15', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 1, 'r': 4},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*fp32', 'in_ptr0': '*fp32', 'in_ptr1': '*i64', 'out_ptr1': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {'xnumel': 1}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3), 'tt.equal_to': (4,)}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused_nll_loss_forward_15', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': False, 'no_x_dim': False, 'num_load': 2, 'num_reduction': 2, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused_nll_loss_forward_15(in_out_ptr0, in_ptr0, in_ptr1, out_ptr1, xnumel, rnumel, XBLOCK : tl.constexpr):
    xnumel = 1
    rnumel = 4
    RBLOCK: tl.constexpr = 4
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:, None]
    xmask = tl.full([XBLOCK, RBLOCK], True, tl.int1)
    rindex = tl.arange(0, RBLOCK)[None, :]
    roffset = 0
    rmask = tl.full([XBLOCK, RBLOCK], True, tl.int1)
    r0 = rindex
    tmp0 = tl.load(in_ptr0 + (r0), None)
    tmp4 = tl.load(in_ptr1 + (r0), None)
    tmp1 = tl.broadcast_to(tmp0, [XBLOCK, RBLOCK])
    tmp3 = tl.sum(tmp1, 1)[:, None]
    tmp5 = tl.broadcast_to(tmp4, [XBLOCK, RBLOCK])
    tmp7 = tl.sum(tmp5, 1)[:, None]
    tmp8 = tmp7.to(tl.float32)
    tmp9 = tmp3 / tmp8
    tl.store(out_ptr1 + (tl.full([XBLOCK, 1], 0, tl.int32)), tmp8, None)
    tl.debug_barrier()
    tl.store(in_out_ptr0 + (tl.full([XBLOCK, 1], 0, tl.int32)), tmp9, None)
''', device_str='cuda')


async_compile.wait(globals())
del async_compile

def call(args):
    primals_1, primals_2, primals_3, primals_4, primals_5, primals_6, primals_7, primals_8, primals_9, primals_10, primals_11, primals_12, primals_13, primals_14, primals_15, primals_16, primals_17, primals_18, primals_19, primals_20, primals_21, primals_22, primals_23, primals_24, primals_25, primals_26, primals_27, primals_28, primals_29, primals_30, primals_31, primals_32, primals_33, primals_34, primals_35, primals_36 = args
    args.clear()
    assert_size_stride(primals_1, (16, 2048), (2048, 1))
    assert_size_stride(primals_2, (1, 20480, 1, 64), (1310720, 64, 64, 1))
    assert_size_stride(primals_3, (1, 20480, 1, 64), (1310720, 64, 64, 1))
    assert_size_stride(primals_4, (8192, 256), (256, 1))
    assert_size_stride(primals_5, (4, ), (1, ))
    assert_size_stride(primals_6, (4, ), (1, ))
    assert_size_stride(primals_7, (256, 256), (256, 1))
    assert_size_stride(primals_8, (256, 256), (256, 1))
    assert_size_stride(primals_9, (256, 256), (256, 1))
    assert_size_stride(primals_10, (256, 256), (256, 1))
    assert_size_stride(primals_11, (1024, 256), (256, 1))
    assert_size_stride(primals_12, (256, 1024), (1024, 1))
    assert_size_stride(primals_13, (8192, 256), (256, 1))
    assert_size_stride(primals_14, (256, 256), (256, 1))
    assert_size_stride(primals_15, (256, 256), (256, 1))
    assert_size_stride(primals_16, (256, 256), (256, 1))
    assert_size_stride(primals_17, (2, 32), (32, 1))
    assert_size_stride(primals_18, (256, 256), (256, 1))
    assert_size_stride(primals_19, (1024, 256), (256, 1))
    assert_size_stride(primals_20, (256, 1024), (1024, 1))
    assert_size_stride(primals_21, (256, 256), (256, 1))
    assert_size_stride(primals_22, (256, 256), (256, 1))
    assert_size_stride(primals_23, (256, 256), (256, 1))
    assert_size_stride(primals_24, (256, 256), (256, 1))
    assert_size_stride(primals_25, (1024, 256), (256, 1))
    assert_size_stride(primals_26, (256, 1024), (1024, 1))
    assert_size_stride(primals_27, (8192, 256), (256, 1))
    assert_size_stride(primals_28, (256, 256), (256, 1))
    assert_size_stride(primals_29, (256, 256), (256, 1))
    assert_size_stride(primals_30, (256, 256), (256, 1))
    assert_size_stride(primals_31, (2, 32), (32, 1))
    assert_size_stride(primals_32, (256, 256), (256, 1))
    assert_size_stride(primals_33, (1024, 256), (256, 1))
    assert_size_stride(primals_34, (256, 1024), (1024, 1))
    assert_size_stride(primals_35, (8192, 256), (256, 1))
    assert_size_stride(primals_36, (16, 2048), (2048, 1))
    with torch.cuda._DeviceGuard(0):
        torch.cuda.set_device(0)
        buf0 = empty_strided_cuda((16, 2048, 256), (524288, 256, 1), torch.bfloat16)
        buf1 = empty_strided_cuda((16, 2048, 1), (2048, 1, 32768), torch.float32)
        buf2 = reinterpret_tensor(buf1, (16, 2048, 1), (2048, 1, 1), 0); del buf1  # reuse
        buf3 = empty_strided_cuda((16, 2048, 1), (2048, 1, 32768), torch.float32)
        buf4 = reinterpret_tensor(buf3, (16, 2048, 1), (2048, 1, 1), 0); del buf3  # reuse
        buf6 = empty_strided_cuda((16, 2048, 256), (524288, 256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [x, x_1, mul, mul_1, x_2, rms_norm_1], Original ATen: [aten.embedding, aten._to_copy, aten.pow, aten.mean, aten.add, aten.rsqrt, aten.mul]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_0.run(buf2, buf4, primals_1, primals_4, primals_5, primals_6, buf0, buf6, 32768, 256, grid=grid(32768), stream=stream0)
        del primals_4
        buf5 = empty_strided_cuda((256, 256), (1, 256), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear], Original ATen: [aten._to_copy, aten.t]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_t_1.run(primals_7, buf5, 65536, grid=grid(65536), stream=stream0)
        del primals_7
        buf7 = empty_strided_cuda((32768, 256), (256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf6, (32768, 256), (256, 1), 0), buf5, out=buf7)
        buf8 = empty_strided_cuda((256, 256), (1, 256), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear_1], Original ATen: [aten._to_copy, aten.t]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_t_1.run(primals_8, buf8, 65536, grid=grid(65536), stream=stream0)
        del primals_8
        buf9 = empty_strided_cuda((32768, 256), (256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear_1], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf6, (32768, 256), (256, 1), 0), buf8, out=buf9)
        buf10 = empty_strided_cuda((256, 256), (1, 256), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear_2], Original ATen: [aten._to_copy, aten.t]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_t_1.run(primals_9, buf10, 65536, grid=grid(65536), stream=stream0)
        del primals_9
        buf11 = empty_strided_cuda((32768, 256), (256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear_2], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf6, (32768, 256), (256, 1), 0), buf10, out=buf11)
        buf12 = empty_strided_cuda((16, 2048, 2, 128), (524288, 256, 128, 1), torch.bfloat16)
        buf13 = empty_strided_cuda((16, 2048, 2, 128), (524288, 256, 128, 1), torch.bfloat16)
        buf14 = empty_strided_cuda((16, 2048, 2, 1), (4096, 2, 1, 65536), torch.float32)
        buf16 = empty_strided_cuda((16, 2048, 2, 1), (4096, 2, 1, 65536), torch.float32)
        buf15 = reinterpret_tensor(buf14, (16, 2048, 2, 1), (4096, 2, 1, 1), 0); del buf14  # reuse
        buf17 = reinterpret_tensor(buf16, (16, 2048, 2, 1), (4096, 2, 1, 1), 0); del buf16  # reuse
        buf18 = empty_strided_cuda((16, 2048, 2, 128), (524288, 256, 128, 1), torch.bfloat16)
        buf19 = empty_strided_cuda((16, 2048, 2, 128), (524288, 256, 128, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [q_1, k_1, q_2, k_2], Original ATen: [aten.cat, aten._to_copy, aten.pow, aten.mean, aten.add, aten.rsqrt, aten.mul]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_cat_mean_mul_pow_rsqrt_2.run(buf15, buf17, buf7, primals_2, primals_3, buf9, buf12, buf13, buf18, buf19, 65536, 128, grid=grid(65536), stream=stream0)
        # Topologically Sorted Source Nodes: [y], Original ATen: [aten._scaled_dot_product_flash_attention]
        buf20 = torch.ops.aten._scaled_dot_product_flash_attention.default(reinterpret_tensor(buf18, (16, 2, 2048, 128), (524288, 128, 256, 1), 0), reinterpret_tensor(buf19, (16, 2, 2048, 128), (524288, 128, 256, 1), 0), reinterpret_tensor(buf11, (16, 2, 2048, 128), (524288, 128, 256, 1), 0), 0.0, True, scale=0.08838834764831843)
        buf21 = buf20[0]
        buf22 = buf20[1]
        buf23 = buf20[6]
        buf24 = buf20[7]
        del buf20
        buf26 = empty_strided_cuda((256, 256), (1, 256), torch.bfloat16)
        # Topologically Sorted Source Nodes: [y_2], Original ATen: [aten._to_copy, aten.t]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_t_1.run(primals_10, buf26, 65536, grid=grid(65536), stream=stream0)
        del primals_10
        buf27 = buf9; del buf9  # reuse
        # Topologically Sorted Source Nodes: [y_2], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf21, (32768, 256), (256, 1), 0), buf26, out=buf27)
        buf28 = reinterpret_tensor(buf27, (16, 2048, 256), (524288, 256, 1), 0); del buf27  # reuse
        buf29 = empty_strided_cuda((16, 2048, 1), (2048, 1, 32768), torch.float32)
        buf30 = reinterpret_tensor(buf29, (16, 2048, 1), (2048, 1, 1), 0); del buf29  # reuse
        buf32 = reinterpret_tensor(buf7, (16, 2048, 256), (524288, 256, 1), 0); del buf7  # reuse
        # Topologically Sorted Source Nodes: [x_1, mul, mul_1, x_2, x_3, rms_norm_4], Original ATen: [aten._to_copy, aten.mul, aten.add, aten.pow, aten.mean, aten.rsqrt]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_3.run(buf28, buf30, primals_5, buf0, buf2, primals_6, buf32, 32768, 256, grid=grid(32768), stream=stream0)
        buf31 = empty_strided_cuda((256, 1024), (1, 256), torch.bfloat16)
        # Topologically Sorted Source Nodes: [x_4], Original ATen: [aten._to_copy, aten.t]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_t_4.run(primals_11, buf31, 262144, grid=grid(262144), stream=stream0)
        del primals_11
        buf33 = empty_strided_cuda((32768, 1024), (1024, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [x_4], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf32, (32768, 256), (256, 1), 0), buf31, out=buf33)
        buf34 = empty_strided_cuda((1024, 256), (1, 1024), torch.bfloat16)
        # Topologically Sorted Source Nodes: [x_6], Original ATen: [aten._to_copy, aten.t]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_t_4.run(primals_12, buf34, 262144, grid=grid(262144), stream=stream0)
        del primals_12
        buf35 = empty_strided_cuda((16, 2048, 1024), (2097152, 1024, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [relu, x_5, x_6], Original ATen: [aten.relu, aten._to_copy, aten.pow]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_pow_relu_5.run(buf33, buf35, 33554432, grid=grid(33554432), stream=stream0)
        buf36 = empty_strided_cuda((32768, 256), (256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [x_6], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf35, (32768, 1024), (1024, 1), 0), buf34, out=buf36)
        buf37 = reinterpret_tensor(buf36, (16, 2048, 256), (524288, 256, 1), 0); del buf36  # reuse
        buf38 = empty_strided_cuda((16, 2048, 256), (524288, 256, 1), torch.bfloat16)
        buf40 = empty_strided_cuda((16, 2048, 1), (2048, 1, 32768), torch.float32)
        buf41 = reinterpret_tensor(buf40, (16, 2048, 1), (2048, 1, 1), 0); del buf40  # reuse
        buf43 = empty_strided_cuda((16, 2048, 256), (524288, 256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [x_1, x_7, mul_10, mul_11, x_8, rms_norm_5], Original ATen: [aten._to_copy, aten.mul, aten.add, aten.pow, aten.mean, aten.rsqrt]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_6.run(buf37, buf41, buf28, primals_5, primals_6, buf0, buf2, buf38, buf43, 32768, 256, grid=grid(32768), stream=stream0)
        buf47 = empty_strided_cuda((256, 256), (1, 256), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear_8], Original ATen: [aten._to_copy, aten.t]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_t_1.run(primals_16, buf47, 65536, grid=grid(65536), stream=stream0)
        del primals_16
        buf48 = empty_strided_cuda((32768, 256), (256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear_8], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf43, (32768, 256), (256, 1), 0), buf47, out=buf48)
        buf49 = empty_strided_cuda((32, 2), (1, 32), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear_9], Original ATen: [aten._to_copy, aten.t]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_t_7.run(primals_17, buf49, 64, grid=grid(64), stream=stream0)
        del primals_17
        buf50 = empty_strided_cuda((32768, 2), (2, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear_9], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf43, (32768, 32), (256, 1), 0), buf49, out=buf50)
        buf39 = empty_strided_cuda((16, 2048, 256), (524288, 256, 1), torch.bfloat16)
        buf59 = reinterpret_tensor(buf48, (16, 2048, 2, 128), (524288, 256, 128, 1), 0); del buf48  # reuse
        # Topologically Sorted Source Nodes: [ve, mul_13, v_4], Original ATen: [aten.embedding, aten.mul, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_embedding_mul_8.run(buf59, primals_1, primals_13, buf50, buf39, 8388608, grid=grid(8388608), stream=stream0)
        del primals_13
        buf42 = empty_strided_cuda((256, 256), (1, 256), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear_6], Original ATen: [aten._to_copy, aten.t]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_t_1.run(primals_14, buf42, 65536, grid=grid(65536), stream=stream0)
        del primals_14
        buf44 = empty_strided_cuda((32768, 256), (256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear_6], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf43, (32768, 256), (256, 1), 0), buf42, out=buf44)
        buf45 = empty_strided_cuda((256, 256), (1, 256), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear_7], Original ATen: [aten._to_copy, aten.t]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_t_1.run(primals_15, buf45, 65536, grid=grid(65536), stream=stream0)
        del primals_15
        buf46 = empty_strided_cuda((32768, 256), (256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear_7], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf43, (32768, 256), (256, 1), 0), buf45, out=buf46)
        buf51 = empty_strided_cuda((16, 2048, 2, 128), (524288, 256, 128, 1), torch.bfloat16)
        buf52 = empty_strided_cuda((16, 2048, 2, 128), (524288, 256, 128, 1), torch.bfloat16)
        buf53 = empty_strided_cuda((16, 2048, 2, 1), (4096, 2, 1, 65536), torch.float32)
        buf55 = empty_strided_cuda((16, 2048, 2, 1), (4096, 2, 1, 65536), torch.float32)
        buf54 = reinterpret_tensor(buf53, (16, 2048, 2, 1), (4096, 2, 1, 1), 0); del buf53  # reuse
        buf56 = reinterpret_tensor(buf55, (16, 2048, 2, 1), (4096, 2, 1, 1), 0); del buf55  # reuse
        buf57 = empty_strided_cuda((16, 2048, 2, 128), (524288, 256, 128, 1), torch.bfloat16)
        buf58 = empty_strided_cuda((16, 2048, 2, 128), (524288, 256, 128, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [q_5, k_6, q_6, k_7], Original ATen: [aten.cat, aten._to_copy, aten.pow, aten.mean, aten.add, aten.rsqrt, aten.mul]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_cat_mean_mul_pow_rsqrt_2.run(buf54, buf56, buf44, primals_2, primals_3, buf46, buf51, buf52, buf57, buf58, 65536, 128, grid=grid(65536), stream=stream0)
        # Topologically Sorted Source Nodes: [y_3], Original ATen: [aten._scaled_dot_product_flash_attention]
        buf60 = torch.ops.aten._scaled_dot_product_flash_attention.default(reinterpret_tensor(buf57, (16, 2, 2048, 128), (524288, 128, 256, 1), 0), reinterpret_tensor(buf58, (16, 2, 2048, 128), (524288, 128, 256, 1), 0), reinterpret_tensor(buf59, (16, 2, 2048, 128), (524288, 128, 256, 1), 0), 0.0, True, scale=0.08838834764831843)
        buf61 = buf60[0]
        buf62 = buf60[1]
        buf63 = buf60[6]
        buf64 = buf60[7]
        del buf60
        buf66 = empty_strided_cuda((256, 256), (1, 256), torch.bfloat16)
        # Topologically Sorted Source Nodes: [y_5], Original ATen: [aten._to_copy, aten.t]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_t_1.run(primals_18, buf66, 65536, grid=grid(65536), stream=stream0)
        del primals_18
        buf67 = buf46; del buf46  # reuse
        # Topologically Sorted Source Nodes: [y_5], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf61, (32768, 256), (256, 1), 0), buf66, out=buf67)
        buf68 = reinterpret_tensor(buf67, (16, 2048, 256), (524288, 256, 1), 0); del buf67  # reuse
        buf69 = empty_strided_cuda((16, 2048, 1), (2048, 1, 32768), torch.float32)
        buf70 = reinterpret_tensor(buf69, (16, 2048, 1), (2048, 1, 1), 0); del buf69  # reuse
        buf72 = reinterpret_tensor(buf44, (16, 2048, 256), (524288, 256, 1), 0); del buf44  # reuse
        # Topologically Sorted Source Nodes: [x_9, rms_norm_8], Original ATen: [aten.add, aten._to_copy, aten.pow, aten.mean, aten.rsqrt, aten.mul]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_9.run(buf68, buf70, buf38, buf72, 32768, 256, grid=grid(32768), stream=stream0)
        buf71 = empty_strided_cuda((256, 1024), (1, 256), torch.bfloat16)
        # Topologically Sorted Source Nodes: [x_10], Original ATen: [aten._to_copy, aten.t]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_t_4.run(primals_19, buf71, 262144, grid=grid(262144), stream=stream0)
        del primals_19
        buf73 = empty_strided_cuda((32768, 1024), (1024, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [x_10], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf72, (32768, 256), (256, 1), 0), buf71, out=buf73)
        buf74 = empty_strided_cuda((1024, 256), (1, 1024), torch.bfloat16)
        # Topologically Sorted Source Nodes: [x_12], Original ATen: [aten._to_copy, aten.t]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_t_4.run(primals_20, buf74, 262144, grid=grid(262144), stream=stream0)
        del primals_20
        buf75 = empty_strided_cuda((16, 2048, 1024), (2097152, 1024, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [relu_1, x_11, x_12], Original ATen: [aten.relu, aten._to_copy, aten.pow]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_pow_relu_5.run(buf73, buf75, 33554432, grid=grid(33554432), stream=stream0)
        buf76 = empty_strided_cuda((32768, 256), (256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [x_12], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf75, (32768, 1024), (1024, 1), 0), buf74, out=buf76)
        buf77 = reinterpret_tensor(buf76, (16, 2048, 256), (524288, 256, 1), 0); del buf76  # reuse
        buf78 = empty_strided_cuda((16, 2048, 256), (524288, 256, 1), torch.bfloat16)
        buf79 = empty_strided_cuda((16, 2048, 1), (2048, 1, 32768), torch.float32)
        buf80 = reinterpret_tensor(buf79, (16, 2048, 1), (2048, 1, 1), 0); del buf79  # reuse
        buf82 = empty_strided_cuda((16, 2048, 256), (524288, 256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [x_1, x_13, mul_22, mul_23, x_14, rms_norm_9], Original ATen: [aten._to_copy, aten.mul, aten.add, aten.pow, aten.mean, aten.rsqrt]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_10.run(buf77, buf80, buf68, primals_5, primals_6, buf0, buf2, buf78, buf82, 32768, 256, grid=grid(32768), stream=stream0)
        buf81 = empty_strided_cuda((256, 256), (1, 256), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear_13], Original ATen: [aten._to_copy, aten.t]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_t_1.run(primals_21, buf81, 65536, grid=grid(65536), stream=stream0)
        del primals_21
        buf83 = empty_strided_cuda((32768, 256), (256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear_13], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf82, (32768, 256), (256, 1), 0), buf81, out=buf83)
        buf84 = empty_strided_cuda((256, 256), (1, 256), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear_14], Original ATen: [aten._to_copy, aten.t]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_t_1.run(primals_22, buf84, 65536, grid=grid(65536), stream=stream0)
        del primals_22
        buf85 = empty_strided_cuda((32768, 256), (256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear_14], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf82, (32768, 256), (256, 1), 0), buf84, out=buf85)
        buf86 = empty_strided_cuda((256, 256), (1, 256), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear_15], Original ATen: [aten._to_copy, aten.t]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_t_1.run(primals_23, buf86, 65536, grid=grid(65536), stream=stream0)
        del primals_23
        buf87 = empty_strided_cuda((32768, 256), (256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear_15], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf82, (32768, 256), (256, 1), 0), buf86, out=buf87)
        buf88 = empty_strided_cuda((16, 2048, 2, 128), (524288, 256, 128, 1), torch.bfloat16)
        buf89 = empty_strided_cuda((16, 2048, 2, 128), (524288, 256, 128, 1), torch.bfloat16)
        buf90 = empty_strided_cuda((16, 2048, 2, 1), (4096, 2, 1, 65536), torch.float32)
        buf92 = empty_strided_cuda((16, 2048, 2, 1), (4096, 2, 1, 65536), torch.float32)
        buf91 = reinterpret_tensor(buf90, (16, 2048, 2, 1), (4096, 2, 1, 1), 0); del buf90  # reuse
        buf93 = reinterpret_tensor(buf92, (16, 2048, 2, 1), (4096, 2, 1, 1), 0); del buf92  # reuse
        buf94 = empty_strided_cuda((16, 2048, 2, 128), (524288, 256, 128, 1), torch.bfloat16)
        buf95 = empty_strided_cuda((16, 2048, 2, 128), (524288, 256, 128, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [q_9, k_11, q_10, k_12], Original ATen: [aten.cat, aten._to_copy, aten.pow, aten.mean, aten.add, aten.rsqrt, aten.mul]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_cat_mean_mul_pow_rsqrt_2.run(buf91, buf93, buf83, primals_2, primals_3, buf85, buf88, buf89, buf94, buf95, 65536, 128, grid=grid(65536), stream=stream0)
        # Topologically Sorted Source Nodes: [y_6], Original ATen: [aten._scaled_dot_product_flash_attention]
        buf96 = torch.ops.aten._scaled_dot_product_flash_attention.default(reinterpret_tensor(buf94, (16, 2, 2048, 128), (524288, 128, 256, 1), 0), reinterpret_tensor(buf95, (16, 2, 2048, 128), (524288, 128, 256, 1), 0), reinterpret_tensor(buf87, (16, 2, 2048, 128), (524288, 128, 256, 1), 0), 0.0, True, scale=0.08838834764831843)
        buf97 = buf96[0]
        buf98 = buf96[1]
        buf99 = buf96[6]
        buf100 = buf96[7]
        del buf96
        buf102 = empty_strided_cuda((256, 256), (1, 256), torch.bfloat16)
        # Topologically Sorted Source Nodes: [y_8], Original ATen: [aten._to_copy, aten.t]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_t_1.run(primals_24, buf102, 65536, grid=grid(65536), stream=stream0)
        del primals_24
        buf103 = buf85; del buf85  # reuse
        # Topologically Sorted Source Nodes: [y_8], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf97, (32768, 256), (256, 1), 0), buf102, out=buf103)
        buf104 = reinterpret_tensor(buf103, (16, 2048, 256), (524288, 256, 1), 0); del buf103  # reuse
        buf105 = empty_strided_cuda((16, 2048, 1), (2048, 1, 32768), torch.float32)
        buf106 = reinterpret_tensor(buf105, (16, 2048, 1), (2048, 1, 1), 0); del buf105  # reuse
        buf108 = reinterpret_tensor(buf83, (16, 2048, 256), (524288, 256, 1), 0); del buf83  # reuse
        # Topologically Sorted Source Nodes: [x_15, rms_norm_12], Original ATen: [aten.add, aten._to_copy, aten.pow, aten.mean, aten.rsqrt, aten.mul]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_9.run(buf104, buf106, buf78, buf108, 32768, 256, grid=grid(32768), stream=stream0)
        buf107 = empty_strided_cuda((256, 1024), (1, 256), torch.bfloat16)
        # Topologically Sorted Source Nodes: [x_16], Original ATen: [aten._to_copy, aten.t]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_t_4.run(primals_25, buf107, 262144, grid=grid(262144), stream=stream0)
        del primals_25
        buf109 = empty_strided_cuda((32768, 1024), (1024, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [x_16], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf108, (32768, 256), (256, 1), 0), buf107, out=buf109)
        buf110 = empty_strided_cuda((1024, 256), (1, 1024), torch.bfloat16)
        # Topologically Sorted Source Nodes: [x_18], Original ATen: [aten._to_copy, aten.t]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_t_4.run(primals_26, buf110, 262144, grid=grid(262144), stream=stream0)
        del primals_26
        buf111 = empty_strided_cuda((16, 2048, 1024), (2097152, 1024, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [relu_2, x_17, x_18], Original ATen: [aten.relu, aten._to_copy, aten.pow]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_pow_relu_5.run(buf109, buf111, 33554432, grid=grid(33554432), stream=stream0)
        buf112 = empty_strided_cuda((32768, 256), (256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [x_18], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf111, (32768, 1024), (1024, 1), 0), buf110, out=buf112)
        buf113 = reinterpret_tensor(buf112, (16, 2048, 256), (524288, 256, 1), 0); del buf112  # reuse
        buf114 = empty_strided_cuda((16, 2048, 256), (524288, 256, 1), torch.bfloat16)
        buf116 = empty_strided_cuda((16, 2048, 1), (2048, 1, 32768), torch.float32)
        buf117 = reinterpret_tensor(buf116, (16, 2048, 1), (2048, 1, 1), 0); del buf116  # reuse
        buf119 = empty_strided_cuda((16, 2048, 256), (524288, 256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [x_1, x_19, mul_32, mul_33, x_20, rms_norm_13], Original ATen: [aten._to_copy, aten.mul, aten.add, aten.pow, aten.mean, aten.rsqrt]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_11.run(buf113, buf117, buf104, primals_5, primals_6, buf0, buf2, buf114, buf119, 32768, 256, grid=grid(32768), stream=stream0)
        buf123 = empty_strided_cuda((256, 256), (1, 256), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear_21], Original ATen: [aten._to_copy, aten.t]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_t_1.run(primals_30, buf123, 65536, grid=grid(65536), stream=stream0)
        del primals_30
        buf124 = empty_strided_cuda((32768, 256), (256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear_21], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf119, (32768, 256), (256, 1), 0), buf123, out=buf124)
        buf125 = empty_strided_cuda((32, 2), (1, 32), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear_22], Original ATen: [aten._to_copy, aten.t]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_t_7.run(primals_31, buf125, 64, grid=grid(64), stream=stream0)
        del primals_31
        buf126 = empty_strided_cuda((32768, 2), (2, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear_22], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf119, (32768, 32), (256, 1), 0), buf125, out=buf126)
        buf115 = empty_strided_cuda((16, 2048, 256), (524288, 256, 1), torch.bfloat16)
        buf135 = reinterpret_tensor(buf124, (16, 2048, 2, 128), (524288, 256, 128, 1), 0); del buf124  # reuse
        # Topologically Sorted Source Nodes: [ve_2, mul_35, v_11], Original ATen: [aten.embedding, aten.mul, aten.add]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_embedding_mul_8.run(buf135, primals_1, primals_27, buf126, buf115, 8388608, grid=grid(8388608), stream=stream0)
        del primals_27
        buf118 = empty_strided_cuda((256, 256), (1, 256), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear_19], Original ATen: [aten._to_copy, aten.t]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_t_1.run(primals_28, buf118, 65536, grid=grid(65536), stream=stream0)
        del primals_28
        buf120 = empty_strided_cuda((32768, 256), (256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear_19], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf119, (32768, 256), (256, 1), 0), buf118, out=buf120)
        buf121 = empty_strided_cuda((256, 256), (1, 256), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear_20], Original ATen: [aten._to_copy, aten.t]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_t_1.run(primals_29, buf121, 65536, grid=grid(65536), stream=stream0)
        del primals_29
        buf122 = empty_strided_cuda((32768, 256), (256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear_20], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf119, (32768, 256), (256, 1), 0), buf121, out=buf122)
        buf127 = empty_strided_cuda((16, 2048, 2, 128), (524288, 256, 128, 1), torch.bfloat16)
        buf128 = empty_strided_cuda((16, 2048, 2, 128), (524288, 256, 128, 1), torch.bfloat16)
        buf129 = empty_strided_cuda((16, 2048, 2, 1), (4096, 2, 1, 65536), torch.float32)
        buf131 = empty_strided_cuda((16, 2048, 2, 1), (4096, 2, 1, 65536), torch.float32)
        buf130 = reinterpret_tensor(buf129, (16, 2048, 2, 1), (4096, 2, 1, 1), 0); del buf129  # reuse
        buf132 = reinterpret_tensor(buf131, (16, 2048, 2, 1), (4096, 2, 1, 1), 0); del buf131  # reuse
        buf133 = empty_strided_cuda((16, 2048, 2, 128), (524288, 256, 128, 1), torch.bfloat16)
        buf134 = empty_strided_cuda((16, 2048, 2, 128), (524288, 256, 128, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [q_13, k_16, q_14, k_17], Original ATen: [aten.cat, aten._to_copy, aten.pow, aten.mean, aten.add, aten.rsqrt, aten.mul]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_cat_mean_mul_pow_rsqrt_2.run(buf130, buf132, buf120, primals_2, primals_3, buf122, buf127, buf128, buf133, buf134, 65536, 128, grid=grid(65536), stream=stream0)
        # Topologically Sorted Source Nodes: [y_9], Original ATen: [aten._scaled_dot_product_flash_attention]
        buf136 = torch.ops.aten._scaled_dot_product_flash_attention.default(reinterpret_tensor(buf133, (16, 2, 2048, 128), (524288, 128, 256, 1), 0), reinterpret_tensor(buf134, (16, 2, 2048, 128), (524288, 128, 256, 1), 0), reinterpret_tensor(buf135, (16, 2, 2048, 128), (524288, 128, 256, 1), 0), 0.0, True, scale=0.08838834764831843)
        buf137 = buf136[0]
        buf138 = buf136[1]
        buf139 = buf136[6]
        buf140 = buf136[7]
        del buf136
        buf142 = empty_strided_cuda((256, 256), (1, 256), torch.bfloat16)
        # Topologically Sorted Source Nodes: [y_11], Original ATen: [aten._to_copy, aten.t]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_t_1.run(primals_32, buf142, 65536, grid=grid(65536), stream=stream0)
        del primals_32
        buf143 = buf122; del buf122  # reuse
        # Topologically Sorted Source Nodes: [y_11], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf137, (32768, 256), (256, 1), 0), buf142, out=buf143)
        buf144 = reinterpret_tensor(buf143, (16, 2048, 256), (524288, 256, 1), 0); del buf143  # reuse
        buf145 = empty_strided_cuda((16, 2048, 1), (2048, 1, 32768), torch.float32)
        buf146 = reinterpret_tensor(buf145, (16, 2048, 1), (2048, 1, 1), 0); del buf145  # reuse
        buf148 = reinterpret_tensor(buf120, (16, 2048, 256), (524288, 256, 1), 0); del buf120  # reuse
        # Topologically Sorted Source Nodes: [x_21, rms_norm_16], Original ATen: [aten.add, aten._to_copy, aten.pow, aten.mean, aten.rsqrt, aten.mul]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_9.run(buf144, buf146, buf114, buf148, 32768, 256, grid=grid(32768), stream=stream0)
        buf147 = empty_strided_cuda((256, 1024), (1, 256), torch.bfloat16)
        # Topologically Sorted Source Nodes: [x_22], Original ATen: [aten._to_copy, aten.t]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_t_4.run(primals_33, buf147, 262144, grid=grid(262144), stream=stream0)
        del primals_33
        buf149 = empty_strided_cuda((32768, 1024), (1024, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [x_22], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf148, (32768, 256), (256, 1), 0), buf147, out=buf149)
        buf150 = empty_strided_cuda((1024, 256), (1, 1024), torch.bfloat16)
        # Topologically Sorted Source Nodes: [x_24], Original ATen: [aten._to_copy, aten.t]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_t_4.run(primals_34, buf150, 262144, grid=grid(262144), stream=stream0)
        del primals_34
        buf151 = empty_strided_cuda((16, 2048, 1024), (2097152, 1024, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [relu_3, x_23, x_24], Original ATen: [aten.relu, aten._to_copy, aten.pow]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_pow_relu_5.run(buf149, buf151, 33554432, grid=grid(33554432), stream=stream0)
        buf152 = empty_strided_cuda((32768, 256), (256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [x_24], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf151, (32768, 1024), (1024, 1), 0), buf150, out=buf152)
        buf153 = reinterpret_tensor(buf152, (16, 2048, 256), (524288, 256, 1), 0); del buf152  # reuse
        buf154 = empty_strided_cuda((16, 2048, 1), (2048, 1, 32768), torch.float32)
        buf155 = reinterpret_tensor(buf154, (16, 2048, 1), (2048, 1, 1), 0); del buf154  # reuse
        buf157 = empty_strided_cuda((16, 2048, 256), (524288, 256, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [x_25, x_26], Original ATen: [aten.add, aten._to_copy, aten.pow, aten.mean, aten.rsqrt, aten.mul]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_9.run(buf153, buf155, buf144, buf157, 32768, 256, grid=grid(32768), stream=stream0)
        buf156 = empty_strided_cuda((256, 8192), (1, 256), torch.bfloat16)
        # Topologically Sorted Source Nodes: [logits], Original ATen: [aten._to_copy, aten.t]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_t_12.run(primals_35, buf156, 2097152, grid=grid(2097152), stream=stream0)
        del primals_35
        buf158 = empty_strided_cuda((32768, 8192), (8192, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [logits], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf157, (32768, 256), (256, 1), 0), buf156, out=buf158)
        buf159 = empty_strided_cuda((32768, 1), (1, 1), torch.float32)
        buf160 = empty_strided_cuda((32768, 1), (1, 32768), torch.float32)
        buf161 = reinterpret_tensor(buf160, (32768, 1), (1, 1), 0); del buf160  # reuse
        # Topologically Sorted Source Nodes: [loss], Original ATen: [aten._log_softmax]
        stream0 = get_raw_stream(0)
        triton_red_fused__log_softmax_13.run(buf161, buf158, buf159, 32768, 8192, grid=grid(32768), stream=stream0)
        buf162 = empty_strided_cuda((4, ), (1, ), torch.int64)
        buf165 = empty_strided_cuda((4, ), (1, ), torch.float32)
        # Topologically Sorted Source Nodes: [loss], Original ATen: [aten.nll_loss_forward]
        stream0 = get_raw_stream(0)
        triton_red_fused_nll_loss_forward_14.run(primals_36, buf158, buf159, buf161, buf162, buf165, 4, 8192, grid=grid(4), stream=stream0)
        buf166 = empty_strided_cuda((), (), torch.float32)
        buf164 = empty_strided_cuda((), (), torch.float32)
        buf167 = buf166; del buf166  # reuse
        # Topologically Sorted Source Nodes: [loss], Original ATen: [aten.nll_loss_forward]
        stream0 = get_raw_stream(0)
        triton_per_fused_nll_loss_forward_15.run(buf167, buf165, buf162, buf164, 1, 4, grid=grid(1), stream=stream0)
        del buf162
        del buf165
    return (buf167, primals_1, primals_5, primals_6, primals_36, reinterpret_tensor(primals_2, (1, 2048, 1, 64), (1310720, 64, 64, 1), 0), reinterpret_tensor(primals_3, (1, 2048, 1, 64), (1310720, 64, 64, 1), 0), buf0, buf2, buf4, reinterpret_tensor(buf6, (32768, 256), (256, 1), 0), buf12, buf13, buf15, buf17, reinterpret_tensor(buf18, (16, 2, 2048, 128), (524288, 128, 256, 1), 0), reinterpret_tensor(buf19, (16, 2, 2048, 128), (524288, 128, 256, 1), 0), reinterpret_tensor(buf11, (16, 2, 2048, 128), (524288, 128, 256, 1), 0), buf21, buf22, buf23, buf24, buf28, buf30, reinterpret_tensor(buf32, (32768, 256), (256, 1), 0), buf33, reinterpret_tensor(buf35, (32768, 1024), (1024, 1), 0), buf37, buf38, buf39, buf41, reinterpret_tensor(buf43, (32768, 256), (256, 1), 0), reinterpret_tensor(buf43, (32768, 32), (256, 1), 0), buf50, buf51, buf52, buf54, buf56, reinterpret_tensor(buf57, (16, 2, 2048, 128), (524288, 128, 256, 1), 0), reinterpret_tensor(buf58, (16, 2, 2048, 128), (524288, 128, 256, 1), 0), reinterpret_tensor(buf59, (16, 2, 2048, 128), (524288, 128, 256, 1), 0), buf61, buf62, buf63, buf64, buf68, buf70, reinterpret_tensor(buf72, (32768, 256), (256, 1), 0), buf73, reinterpret_tensor(buf75, (32768, 1024), (1024, 1), 0), buf77, buf78, buf80, reinterpret_tensor(buf82, (32768, 256), (256, 1), 0), buf88, buf89, buf91, buf93, reinterpret_tensor(buf94, (16, 2, 2048, 128), (524288, 128, 256, 1), 0), reinterpret_tensor(buf95, (16, 2, 2048, 128), (524288, 128, 256, 1), 0), reinterpret_tensor(buf87, (16, 2, 2048, 128), (524288, 128, 256, 1), 0), buf97, buf98, buf99, buf100, buf104, buf106, reinterpret_tensor(buf108, (32768, 256), (256, 1), 0), buf109, reinterpret_tensor(buf111, (32768, 1024), (1024, 1), 0), buf113, buf114, buf115, buf117, reinterpret_tensor(buf119, (32768, 256), (256, 1), 0), reinterpret_tensor(buf119, (32768, 32), (256, 1), 0), buf126, buf127, buf128, buf130, buf132, reinterpret_tensor(buf133, (16, 2, 2048, 128), (524288, 128, 256, 1), 0), reinterpret_tensor(buf134, (16, 2, 2048, 128), (524288, 128, 256, 1), 0), reinterpret_tensor(buf135, (16, 2, 2048, 128), (524288, 128, 256, 1), 0), buf137, buf138, buf139, buf140, buf144, buf146, reinterpret_tensor(buf148, (32768, 256), (256, 1), 0), buf149, reinterpret_tensor(buf151, (32768, 1024), (1024, 1), 0), buf153, buf155, reinterpret_tensor(buf157, (32768, 256), (256, 1), 0), buf158, buf159, buf161, buf164, reinterpret_tensor(buf156, (8192, 256), (256, 1), 0), reinterpret_tensor(buf150, (256, 1024), (1024, 1), 0), reinterpret_tensor(buf147, (1024, 256), (256, 1), 0), reinterpret_tensor(buf142, (256, 256), (256, 1), 0), reinterpret_tensor(buf125, (2, 32), (32, 1), 0), reinterpret_tensor(buf123, (256, 256), (256, 1), 0), reinterpret_tensor(buf121, (256, 256), (256, 1), 0), reinterpret_tensor(buf118, (256, 256), (256, 1), 0), reinterpret_tensor(buf110, (256, 1024), (1024, 1), 0), reinterpret_tensor(buf107, (1024, 256), (256, 1), 0), reinterpret_tensor(buf102, (256, 256), (256, 1), 0), reinterpret_tensor(buf86, (256, 256), (256, 1), 0), reinterpret_tensor(buf84, (256, 256), (256, 1), 0), reinterpret_tensor(buf81, (256, 256), (256, 1), 0), reinterpret_tensor(buf74, (256, 1024), (1024, 1), 0), reinterpret_tensor(buf71, (1024, 256), (256, 1), 0), reinterpret_tensor(buf66, (256, 256), (256, 1), 0), reinterpret_tensor(buf49, (2, 32), (32, 1), 0), reinterpret_tensor(buf47, (256, 256), (256, 1), 0), reinterpret_tensor(buf45, (256, 256), (256, 1), 0), reinterpret_tensor(buf42, (256, 256), (256, 1), 0), reinterpret_tensor(buf34, (256, 1024), (1024, 1), 0), reinterpret_tensor(buf31, (1024, 256), (256, 1), 0), reinterpret_tensor(buf26, (256, 256), (256, 1), 0), reinterpret_tensor(buf10, (256, 256), (256, 1), 0), reinterpret_tensor(buf8, (256, 256), (256, 1), 0), reinterpret_tensor(buf5, (256, 256), (256, 1), 0), )


def benchmark_compiled_module(times=10, repeat=10):
    from torch._dynamo.testing import rand_strided
    from torch._inductor.utils import print_performance
    primals_1 = rand_strided((16, 2048), (2048, 1), device='cuda:0', dtype=torch.int64)
    primals_2 = rand_strided((1, 20480, 1, 64), (1310720, 64, 64, 1), device='cuda:0', dtype=torch.bfloat16)
    primals_3 = rand_strided((1, 20480, 1, 64), (1310720, 64, 64, 1), device='cuda:0', dtype=torch.bfloat16)
    primals_4 = rand_strided((8192, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    primals_5 = rand_strided((4, ), (1, ), device='cuda:0', dtype=torch.float32)
    primals_6 = rand_strided((4, ), (1, ), device='cuda:0', dtype=torch.float32)
    primals_7 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.float32)
    primals_8 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.float32)
    primals_9 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.float32)
    primals_10 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.float32)
    primals_11 = rand_strided((1024, 256), (256, 1), device='cuda:0', dtype=torch.float32)
    primals_12 = rand_strided((256, 1024), (1024, 1), device='cuda:0', dtype=torch.float32)
    primals_13 = rand_strided((8192, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    primals_14 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.float32)
    primals_15 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.float32)
    primals_16 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.float32)
    primals_17 = rand_strided((2, 32), (32, 1), device='cuda:0', dtype=torch.float32)
    primals_18 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.float32)
    primals_19 = rand_strided((1024, 256), (256, 1), device='cuda:0', dtype=torch.float32)
    primals_20 = rand_strided((256, 1024), (1024, 1), device='cuda:0', dtype=torch.float32)
    primals_21 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.float32)
    primals_22 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.float32)
    primals_23 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.float32)
    primals_24 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.float32)
    primals_25 = rand_strided((1024, 256), (256, 1), device='cuda:0', dtype=torch.float32)
    primals_26 = rand_strided((256, 1024), (1024, 1), device='cuda:0', dtype=torch.float32)
    primals_27 = rand_strided((8192, 256), (256, 1), device='cuda:0', dtype=torch.bfloat16)
    primals_28 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.float32)
    primals_29 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.float32)
    primals_30 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.float32)
    primals_31 = rand_strided((2, 32), (32, 1), device='cuda:0', dtype=torch.float32)
    primals_32 = rand_strided((256, 256), (256, 1), device='cuda:0', dtype=torch.float32)
    primals_33 = rand_strided((1024, 256), (256, 1), device='cuda:0', dtype=torch.float32)
    primals_34 = rand_strided((256, 1024), (1024, 1), device='cuda:0', dtype=torch.float32)
    primals_35 = rand_strided((8192, 256), (256, 1), device='cuda:0', dtype=torch.float32)
    primals_36 = rand_strided((16, 2048), (2048, 1), device='cuda:0', dtype=torch.int64)
    fn = lambda: call([primals_1, primals_2, primals_3, primals_4, primals_5, primals_6, primals_7, primals_8, primals_9, primals_10, primals_11, primals_12, primals_13, primals_14, primals_15, primals_16, primals_17, primals_18, primals_19, primals_20, primals_21, primals_22, primals_23, primals_24, primals_25, primals_26, primals_27, primals_28, primals_29, primals_30, primals_31, primals_32, primals_33, primals_34, primals_35, primals_36])
    return print_performance(fn, times=times, repeat=repeat)


if __name__ == "__main__":
    from torch._inductor.wrapper_benchmark import compiled_module_main
    compiled_module_main('None', benchmark_compiled_module)
