# AOT ID: ['8_inference']
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


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/bj/cbjejlmruehozhyar4du7izutnvuezqfaam2ks3cexxfl2f5sbaj.py
# Topologically Sorted Source Nodes: [x, x_1, mul, mul_1, x_2, rms_norm_1], Original ATen: [aten.embedding, aten._to_copy, aten.pow, aten.mean, aten.add, aten.rsqrt, aten.mul]
# Source node to ATen node mapping:
#   mul => mul_1
#   mul_1 => mul_2
#   rms_norm_1 => add_2, convert_element_type_2, convert_element_type_3, mean_1, mul_3, pow_2, rsqrt_1
#   x => embedding
#   x_1 => add, convert_element_type, convert_element_type_1, mean, mul, pow_1, rsqrt
#   x_2 => add_1
# Graph fragment:
#   %embedding : [num_users=1] = call_function[target=torch.ops.aten.embedding.default](args = (%arg3_1, %arg0_1), kwargs = {})
#   %convert_element_type : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%embedding, torch.float32), kwargs = {})
#   %pow_1 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type, 2), kwargs = {})
#   %mean : [num_users=1] = call_function[target=torch.ops.aten.mean.dim](args = (%pow_1, [2], True), kwargs = {})
#   %add : [num_users=1] = call_function[target=torch.ops.aten.add.Scalar](args = (%mean, 0.0078125), kwargs = {})
#   %rsqrt : [num_users=1] = call_function[target=torch.ops.aten.rsqrt.default](args = (%add,), kwargs = {})
#   %mul : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type, %rsqrt), kwargs = {})
#   %convert_element_type_1 : [num_users=7] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul, torch.bfloat16), kwargs = {})
#   %mul_1 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%select, %convert_element_type_1), kwargs = {})
#   %mul_2 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%select_1, %convert_element_type_1), kwargs = {})
#   %add_1 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_1, %mul_2), kwargs = {})
#   %convert_element_type_2 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_1, torch.float32), kwargs = {})
#   %pow_2 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_2, 2), kwargs = {})
#   %mean_1 : [num_users=1] = call_function[target=torch.ops.aten.mean.dim](args = (%pow_2, [2], True), kwargs = {})
#   %add_2 : [num_users=1] = call_function[target=torch.ops.aten.add.Scalar](args = (%mean_1, 0.0078125), kwargs = {})
#   %rsqrt_1 : [num_users=1] = call_function[target=torch.ops.aten.rsqrt.default](args = (%add_2,), kwargs = {})
#   %mul_3 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_2, %rsqrt_1), kwargs = {})
#   %convert_element_type_3 : [num_users=3] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul_3, torch.bfloat16), kwargs = {})
triton_red_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_0 = async_compile.triton('triton_red_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_0', '''
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
    triton_meta={'signature': {'in_ptr0': '*i64', 'in_ptr1': '*bf16', 'in_ptr2': '*fp32', 'in_ptr3': '*fp32', 'out_ptr0': '*fp32', 'out_ptr1': '*bf16', 'out_ptr3': '*bf16', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_red_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_0', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 4, 'num_reduction': 2, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_red_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_0(in_ptr0, in_ptr1, in_ptr2, in_ptr3, out_ptr0, out_ptr1, out_ptr3, xnumel, rnumel, XBLOCK : tl.constexpr, RBLOCK : tl.constexpr):
    xnumel = 32768
    rnumel = 384
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:, None]
    xmask = tl.full([XBLOCK, RBLOCK], True, tl.int1)
    rbase = tl.arange(0, RBLOCK)[None, :]
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (x0), None, eviction_policy='evict_last')
    _tmp10 = tl.full([XBLOCK, RBLOCK], 0, tl.float32)
    for roffset in range(0, rnumel, RBLOCK):
        rindex = roffset + rbase
        rmask = rindex < rnumel
        r1 = rindex
        tmp1 = tl.full([XBLOCK, RBLOCK], 8192, tl.int32)
        tmp2 = tmp0 + tmp1
        tmp3 = tmp0 < 0
        tmp4 = tl.where(tmp3, tmp2, tmp0)
        tl.device_assert((0 <= tmp4) & (tmp4 < 8192), "index out of bounds: 0 <= tmp4 < 8192")
        tmp6 = tl.load(in_ptr1 + (r1 + 384*tmp4), rmask, eviction_policy='evict_last', other=0.0).to(tl.float32)
        tmp7 = tmp6.to(tl.float32)
        tmp8 = tmp7 * tmp7
        tmp9 = tl.broadcast_to(tmp8, [XBLOCK, RBLOCK])
        tmp11 = _tmp10 + tmp9
        _tmp10 = tl.where(rmask, tmp11, _tmp10)
    tmp10 = tl.sum(_tmp10, 1)[:, None]
    tl.store(out_ptr0 + (x0), tmp10, None)
    tmp12 = tl.load(in_ptr2 + (0))
    tmp13 = tl.broadcast_to(tmp12, [XBLOCK, RBLOCK])
    tmp30 = tl.load(in_ptr3 + (0))
    tmp31 = tl.broadcast_to(tmp30, [XBLOCK, RBLOCK])
    _tmp38 = tl.full([XBLOCK, RBLOCK], 0, tl.float32)
    for roffset in range(0, rnumel, RBLOCK):
        rindex = roffset + rbase
        rmask = rindex < rnumel
        r1 = rindex
        tmp14 = tmp13.to(tl.float32)
        tmp15 = tl.full([XBLOCK, RBLOCK], 8192, tl.int32)
        tmp16 = tmp0 + tmp15
        tmp17 = tmp0 < 0
        tmp18 = tl.where(tmp17, tmp16, tmp0)
        tl.device_assert((0 <= tmp18) & (tmp18 < 8192), "index out of bounds: 0 <= tmp18 < 8192")
        tmp20 = tl.load(in_ptr1 + (r1 + 384*tmp18), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp21 = tmp20.to(tl.float32)
        tmp22 = 384.0
        tmp23 = tmp10 / tmp22
        tmp24 = 0.0078125
        tmp25 = tmp23 + tmp24
        tmp26 = libdevice.rsqrt(tmp25)
        tmp27 = tmp21 * tmp26
        tmp28 = tmp27.to(tl.float32)
        tmp29 = tmp14 * tmp28
        tmp32 = tmp31.to(tl.float32)
        tmp33 = tmp32 * tmp28
        tmp34 = tmp29 + tmp33
        tmp35 = tmp34.to(tl.float32)
        tmp36 = tmp35 * tmp35
        tmp37 = tl.broadcast_to(tmp36, [XBLOCK, RBLOCK])
        tmp39 = _tmp38 + tmp37
        _tmp38 = tl.where(rmask, tmp39, _tmp38)
        tl.store(out_ptr1 + (r1 + 384*x0), tmp34, rmask)
    tmp38 = tl.sum(_tmp38, 1)[:, None]
    for roffset in range(0, rnumel, RBLOCK):
        rindex = roffset + rbase
        rmask = rindex < rnumel
        r1 = rindex
        tmp40 = tl.load(out_ptr1 + (r1 + 384*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp41 = tmp40.to(tl.float32)
        tmp42 = 384.0
        tmp43 = tmp38 / tmp42
        tmp44 = 0.0078125
        tmp45 = tmp43 + tmp44
        tmp46 = libdevice.rsqrt(tmp45)
        tmp47 = tmp41 * tmp46
        tmp48 = tmp47.to(tl.float32)
        tl.store(out_ptr3 + (r1 + 384*x0), tmp48, rmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/wp/cwpkz7bgp3gqkpsxjcbjflzfgljacifjmykwg4etlzkb7epvdjzf.py
# Topologically Sorted Source Nodes: [linear], Original ATen: [aten._to_copy]
# Source node to ATen node mapping:
#   linear => convert_element_type_4
# Graph fragment:
#   %convert_element_type_4 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%arg6_1, torch.bfloat16), kwargs = {})
triton_poi_fused__to_copy_1 = async_compile.triton('triton_poi_fused__to_copy_1', '''
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
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused__to_copy_1', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 1, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused__to_copy_1(in_ptr0, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 147456
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (x0), None)
    tmp1 = tmp0.to(tl.float32)
    tl.store(out_ptr0 + (x0), tmp1, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/og/cogloc6mqgp3f5ygvvjn5o6w6gxlsakivknv4kkeoexdmu4uthve.py
# Topologically Sorted Source Nodes: [q_1, q_2, k_1, k_2, y], Original ATen: [aten.cat, aten._to_copy, aten.pow, aten.mean, aten._scaled_dot_product_flash_attention]
# Source node to ATen node mapping:
#   k_1 => cat_1
#   k_2 => convert_element_type_15, mean_3, pow_4
#   q_1 => cat
#   q_2 => convert_element_type_13, mean_2, pow_3
#   y => _scaled_dot_product_flash_attention
# Graph fragment:
#   %cat : [num_users=1] = call_function[target=torch.ops.aten.cat.default](args = ([%add_3, %add_4], 3), kwargs = {})
#   %convert_element_type_13 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%cat, torch.float32), kwargs = {})
#   %pow_3 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_13, 2), kwargs = {})
#   %mean_2 : [num_users=1] = call_function[target=torch.ops.aten.mean.dim](args = (%pow_3, [3], True), kwargs = {})
#   %cat_1 : [num_users=1] = call_function[target=torch.ops.aten.cat.default](args = ([%add_5, %add_6], 3), kwargs = {})
#   %convert_element_type_15 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%cat_1, torch.float32), kwargs = {})
#   %pow_4 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_15, 2), kwargs = {})
#   %mean_3 : [num_users=1] = call_function[target=torch.ops.aten.mean.dim](args = (%pow_4, [3], True), kwargs = {})
#   %_scaled_dot_product_flash_attention : [num_users=1] = call_function[target=torch.ops.aten._scaled_dot_product_flash_attention.default](args = (%permute_3, %permute_4, %permute_5, 0.0, True), kwargs = {scale: 0.08838834764831843})
triton_per_fused__scaled_dot_product_flash_attention__to_copy_cat_mean_pow_2 = async_compile.triton('triton_per_fused__scaled_dot_product_flash_attention__to_copy_cat_mean_pow_2', '''
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
    triton_meta={'signature': {'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'in_ptr3': '*bf16', 'out_ptr3': '*bf16', 'out_ptr5': '*bf16', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__scaled_dot_product_flash_attention__to_copy_cat_mean_pow_2', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 12, 'num_reduction': 2, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__scaled_dot_product_flash_attention__to_copy_cat_mean_pow_2(in_ptr0, in_ptr1, in_ptr2, in_ptr3, out_ptr3, out_ptr5, xnumel, rnumel, XBLOCK : tl.constexpr):
    xnumel = 98304
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
    x1 = ((xindex // 3) % 2048)
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
    tmp28 = tmp27.to(tl.float32)
    tmp29 = tl.load(in_ptr3 + (128*x4 + (r3)), tmp4, eviction_policy='evict_last', other=0.0).to(tl.float32)
    tmp30 = tmp29 * tmp6
    tmp31 = tl.load(in_ptr3 + (64 + 128*x4 + (r3)), tmp4, eviction_policy='evict_last', other=0.0).to(tl.float32)
    tmp32 = tmp31 * tmp9
    tmp33 = tmp30 + tmp32
    tmp34 = tl.full(tmp33.shape, 0.0, tmp33.dtype)
    tmp35 = tl.where(tmp4, tmp33, tmp34)
    tmp36 = tl.load(in_ptr3 + (128*x4 + ((-64) + r3)), tmp14, eviction_policy='evict_last', other=0.0).to(tl.float32)
    tmp37 = tmp36 * tmp19
    tmp38 = tl.load(in_ptr3 + (64 + 128*x4 + ((-64) + r3)), tmp14, eviction_policy='evict_last', other=0.0).to(tl.float32)
    tmp39 = tmp38 * tmp22
    tmp40 = tmp37 + tmp39
    tmp41 = tl.full(tmp40.shape, 0.0, tmp40.dtype)
    tmp42 = tl.where(tmp14, tmp40, tmp41)
    tmp43 = tl.where(tmp4, tmp35, tmp42)
    tmp44 = tmp43.to(tl.float32)
    tmp45 = tmp28 * tmp28
    tmp46 = tl.broadcast_to(tmp45, [XBLOCK, RBLOCK])
    tmp48 = tl.sum(tmp46, 1)[:, None]
    tmp49 = 128.0
    tmp50 = tmp48 / tmp49
    tmp51 = 0.0078125
    tmp52 = tmp50 + tmp51
    tmp53 = libdevice.rsqrt(tmp52)
    tmp54 = tmp28 * tmp53
    tmp55 = tmp54.to(tl.float32)
    tmp56 = tmp44 * tmp44
    tmp57 = tl.broadcast_to(tmp56, [XBLOCK, RBLOCK])
    tmp59 = tl.sum(tmp57, 1)[:, None]
    tmp60 = tmp59 / tmp49
    tmp61 = tmp60 + tmp51
    tmp62 = libdevice.rsqrt(tmp61)
    tmp63 = tmp44 * tmp62
    tmp64 = tmp63.to(tl.float32)
    tl.store(out_ptr3 + (r3 + 128*x4), tmp55, None)
    tl.store(out_ptr5 + (r3 + 128*x4), tmp64, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/yw/cywicfomo5ljuzpit3tuh7fa4akicz2k2q5c6ldeozcb7b4vt3ow.py
# Topologically Sorted Source Nodes: [x_3, rms_norm_4], Original ATen: [aten.add, aten._to_copy, aten.pow, aten.mean, aten.rsqrt, aten.mul]
# Source node to ATen node mapping:
#   rms_norm_4 => add_10, convert_element_type_20, convert_element_type_21, mean_4, mul_14, pow_5, rsqrt_4
#   x_3 => add_9
# Graph fragment:
#   %add_9 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_1, %view_13), kwargs = {})
#   %convert_element_type_20 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_9, torch.float32), kwargs = {})
#   %pow_5 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_20, 2), kwargs = {})
#   %mean_4 : [num_users=1] = call_function[target=torch.ops.aten.mean.dim](args = (%pow_5, [2], True), kwargs = {})
#   %add_10 : [num_users=1] = call_function[target=torch.ops.aten.add.Scalar](args = (%mean_4, 0.0078125), kwargs = {})
#   %rsqrt_4 : [num_users=1] = call_function[target=torch.ops.aten.rsqrt.default](args = (%add_10,), kwargs = {})
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
    size_hints={'x': 32768, 'r': 512},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'out_ptr1': '*bf16', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_3', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': True, 'num_load': 2, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_3(in_ptr0, in_ptr1, out_ptr1, xnumel, rnumel):
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
    tmp2 = tmp0 + tmp1
    tmp3 = tmp2.to(tl.float32)
    tmp4 = tmp3 * tmp3
    tmp5 = tl.broadcast_to(tmp4, [RBLOCK])
    tmp7 = tl.where(rmask, tmp5, 0)
    tmp8 = triton_helpers.promote_to_tensor(tl.sum(tmp7, 0))
    tmp9 = 384.0
    tmp10 = tmp8 / tmp9
    tmp11 = 0.0078125
    tmp12 = tmp10 + tmp11
    tmp13 = libdevice.rsqrt(tmp12)
    tmp14 = tmp3 * tmp13
    tmp15 = tmp14.to(tl.float32)
    tl.store(out_ptr1 + (r1 + 384*x0), tmp15, rmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/76/c76qiisymznuc4tbp4kobdaovzkrgckjn4uaqvaeb4qu255wzytu.py
# Topologically Sorted Source Nodes: [x_4], Original ATen: [aten._to_copy]
# Source node to ATen node mapping:
#   x_4 => convert_element_type_22
# Graph fragment:
#   %convert_element_type_22 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%arg10_1, torch.bfloat16), kwargs = {})
triton_poi_fused__to_copy_4 = async_compile.triton('triton_poi_fused__to_copy_4', '''
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
    triton_meta={'signature': {'in_ptr0': '*fp32', 'out_ptr0': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused__to_copy_4', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 1, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused__to_copy_4(in_ptr0, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 589824
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (x0), None)
    tmp1 = tmp0.to(tl.float32)
    tl.store(out_ptr0 + (x0), tmp1, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/gm/cgmwqdl534tv4kysn5hwnpmpq42ujcxa7zbko6bexhys5lrrswtp.py
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
    size_hints={'x': 67108864}, 
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused__to_copy_pow_relu_5', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 1, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused__to_copy_pow_relu_5(in_out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 50331648
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = xindex
    tmp0 = tl.load(in_out_ptr0 + (x0), None).to(tl.float32)
    tmp1 = tl.full([1], 0, tl.int32)
    tmp2 = triton_helpers.maximum(tmp1, tmp0)
    tmp3 = tmp2.to(tl.float32)
    tmp4 = tmp3 * tmp3
    tmp5 = tmp4.to(tl.float32)
    tl.store(in_out_ptr0 + (x0), tmp5, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/w2/cw2777lujsclqa5prxerwie7oxj2tutj2iliv2kkhe3wmwzp35vs.py
# Topologically Sorted Source Nodes: [x, x_1, x_3, x_7, mul_10, mul_11, x_8, rms_norm_5], Original ATen: [aten.embedding, aten._to_copy, aten.pow, aten.mean, aten.add, aten.rsqrt, aten.mul]
# Source node to ATen node mapping:
#   mul_10 => mul_15
#   mul_11 => mul_16
#   rms_norm_5 => add_13, convert_element_type_30, convert_element_type_31, mean_5, mul_17, pow_7, rsqrt_5
#   x => embedding
#   x_1 => add, convert_element_type, convert_element_type_1, mean, mul, pow_1, rsqrt
#   x_3 => add_9
#   x_7 => add_11
#   x_8 => add_12
# Graph fragment:
#   %embedding : [num_users=1] = call_function[target=torch.ops.aten.embedding.default](args = (%arg3_1, %arg0_1), kwargs = {})
#   %convert_element_type : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%embedding, torch.float32), kwargs = {})
#   %pow_1 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type, 2), kwargs = {})
#   %mean : [num_users=1] = call_function[target=torch.ops.aten.mean.dim](args = (%pow_1, [2], True), kwargs = {})
#   %add : [num_users=1] = call_function[target=torch.ops.aten.add.Scalar](args = (%mean, 0.0078125), kwargs = {})
#   %rsqrt : [num_users=1] = call_function[target=torch.ops.aten.rsqrt.default](args = (%add,), kwargs = {})
#   %mul : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type, %rsqrt), kwargs = {})
#   %convert_element_type_1 : [num_users=7] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul, torch.bfloat16), kwargs = {})
#   %add_9 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_1, %view_13), kwargs = {})
#   %add_11 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_9, %view_17), kwargs = {})
#   %mul_15 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%select_2, %add_11), kwargs = {})
#   %mul_16 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%select_3, %convert_element_type_1), kwargs = {})
#   %add_12 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_15, %mul_16), kwargs = {})
#   %convert_element_type_30 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_12, torch.float32), kwargs = {})
#   %pow_7 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_30, 2), kwargs = {})
#   %mean_5 : [num_users=1] = call_function[target=torch.ops.aten.mean.dim](args = (%pow_7, [2], True), kwargs = {})
#   %add_13 : [num_users=1] = call_function[target=torch.ops.aten.add.Scalar](args = (%mean_5, 0.0078125), kwargs = {})
#   %rsqrt_5 : [num_users=1] = call_function[target=torch.ops.aten.rsqrt.default](args = (%add_13,), kwargs = {})
#   %mul_17 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_30, %rsqrt_5), kwargs = {})
#   %convert_element_type_31 : [num_users=4] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul_17, torch.bfloat16), kwargs = {})
triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_6 = async_compile.triton('triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_6', '''
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
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*fp32', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'in_ptr3': '*fp32', 'in_ptr4': '*i64', 'in_ptr5': '*bf16', 'in_ptr6': '*fp32', 'out_ptr1': '*bf16', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_6', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': True, 'num_load': 7, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_6(in_out_ptr0, in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, in_ptr5, in_ptr6, out_ptr1, xnumel, rnumel):
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
    tmp0 = tl.load(in_ptr0 + (1))
    tmp1 = tl.broadcast_to(tmp0, [RBLOCK])
    tmp3 = tl.load(in_out_ptr0 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp4 = tl.load(in_ptr1 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp6 = tl.load(in_ptr2 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp9 = tl.load(in_ptr3 + (1))
    tmp10 = tl.broadcast_to(tmp9, [RBLOCK])
    tmp12 = tl.load(in_ptr4 + (x0), None, eviction_policy='evict_last')
    tmp20 = tl.load(in_ptr6 + (x0), None, eviction_policy='evict_last')
    tmp2 = tmp1.to(tl.float32)
    tmp5 = tmp3 + tmp4
    tmp7 = tmp5 + tmp6
    tmp8 = tmp2 * tmp7
    tmp11 = tmp10.to(tl.float32)
    tmp13 = tl.full([RBLOCK], 8192, tl.int32)
    tmp14 = tmp12 + tmp13
    tmp15 = tmp12 < 0
    tmp16 = tl.where(tmp15, tmp14, tmp12)
    tl.device_assert((0 <= tmp16) & (tmp16 < 8192), "index out of bounds: 0 <= tmp16 < 8192")
    tmp18 = tl.load(in_ptr5 + (r1 + 384*tmp16), rmask, other=0.0).to(tl.float32)
    tmp19 = tmp18.to(tl.float32)
    tmp21 = 384.0
    tmp22 = tmp20 / tmp21
    tmp23 = 0.0078125
    tmp24 = tmp22 + tmp23
    tmp25 = libdevice.rsqrt(tmp24)
    tmp26 = tmp19 * tmp25
    tmp27 = tmp26.to(tl.float32)
    tmp28 = tmp11 * tmp27
    tmp29 = tmp8 + tmp28
    tmp30 = tmp29.to(tl.float32)
    tmp31 = tmp30 * tmp30
    tmp32 = tl.broadcast_to(tmp31, [RBLOCK])
    tmp34 = tl.where(rmask, tmp32, 0)
    tmp35 = triton_helpers.promote_to_tensor(tl.sum(tmp34, 0))
    tmp36 = tmp35 / tmp21
    tmp37 = tmp36 + tmp23
    tmp38 = libdevice.rsqrt(tmp37)
    tmp39 = tmp30 * tmp38
    tmp40 = tmp39.to(tl.float32)
    tl.store(in_out_ptr0 + (r1 + 384*x0), tmp29, rmask)
    tl.store(out_ptr1 + (r1 + 384*x0), tmp40, rmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/dt/cdtx4wps3g6i24rt3gkdrzvwdrbx4j4irjcqzx5yy4jw4bxis4da.py
# Topologically Sorted Source Nodes: [linear_9], Original ATen: [aten._to_copy]
# Source node to ATen node mapping:
#   linear_9 => convert_element_type_41
# Graph fragment:
#   %convert_element_type_41 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%arg16_1, torch.bfloat16), kwargs = {})
triton_poi_fused__to_copy_7 = async_compile.triton('triton_poi_fused__to_copy_7', '''
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
    triton_meta={'signature': {'in_ptr0': '*fp32', 'out_ptr0': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused__to_copy_7', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 1, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused__to_copy_7(in_ptr0, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 96
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = xindex < xnumel
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (x0), xmask)
    tmp1 = tmp0.to(tl.float32)
    tl.store(out_ptr0 + (x0), tmp1, xmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/2a/c2apjib5l66j6ivaqnhofzfplaev2qb5x567x55vdecb7iybe6co.py
# Topologically Sorted Source Nodes: [y_3], Original ATen: [aten._scaled_dot_product_flash_attention]
# Source node to ATen node mapping:
#   y_3 => _scaled_dot_product_flash_attention_1
# Graph fragment:
#   %_scaled_dot_product_flash_attention_1 : [num_users=1] = call_function[target=torch.ops.aten._scaled_dot_product_flash_attention.default](args = (%permute_14, %permute_15, %permute_16, 0.0, True), kwargs = {scale: 0.08838834764831843})
triton_poi_fused__scaled_dot_product_flash_attention_8 = async_compile.triton('triton_poi_fused__scaled_dot_product_flash_attention_8', '''
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
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'in_ptr1': '*i64', 'in_ptr2': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused__scaled_dot_product_flash_attention_8', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 3, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused__scaled_dot_product_flash_attention_8(in_out_ptr0, in_ptr0, in_ptr1, in_ptr2, xnumel, XBLOCK : tl.constexpr):
    xnumel = 12582912
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x3 = xindex
    x4 = xindex // 128
    x2 = xindex // 384
    x5 = (xindex % 384)
    tmp0 = tl.load(in_out_ptr0 + (x3), None).to(tl.float32)
    tmp1 = tl.load(in_ptr0 + (x4), None, eviction_policy='evict_last').to(tl.float32)
    tmp5 = tl.load(in_ptr1 + (x2), None, eviction_policy='evict_last')
    tmp2 = tl.sigmoid(tmp1)
    tmp3 = 2.0
    tmp4 = tmp2 * tmp3
    tmp6 = tl.full([XBLOCK], 8192, tl.int32)
    tmp7 = tmp5 + tmp6
    tmp8 = tmp5 < 0
    tmp9 = tl.where(tmp8, tmp7, tmp5)
    tl.device_assert((0 <= tmp9) & (tmp9 < 8192), "index out of bounds: 0 <= tmp9 < 8192")
    tmp11 = tl.load(in_ptr2 + (x5 + 384*tmp9), None).to(tl.float32)
    tmp12 = tmp4 * tmp11
    tmp13 = tmp0 + tmp12
    tl.store(in_out_ptr0 + (x3), tmp13, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/cu/ccu3i3tchxul2okg746as4xyh6wbvaels72rhku4diqbbiqhorn4.py
# Topologically Sorted Source Nodes: [x, x_1, x_9, x_13, mul_22, mul_23, x_14, rms_norm_9], Original ATen: [aten.embedding, aten._to_copy, aten.pow, aten.mean, aten.add, aten.rsqrt, aten.mul]
# Source node to ATen node mapping:
#   mul_22 => mul_31
#   mul_23 => mul_32
#   rms_norm_9 => add_25, convert_element_type_61, convert_element_type_62, mean_9, mul_33, pow_12, rsqrt_9
#   x => embedding
#   x_1 => add, convert_element_type, convert_element_type_1, mean, mul, pow_1, rsqrt
#   x_13 => add_23
#   x_14 => add_24
#   x_9 => add_21
# Graph fragment:
#   %embedding : [num_users=1] = call_function[target=torch.ops.aten.embedding.default](args = (%arg3_1, %arg0_1), kwargs = {})
#   %convert_element_type : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%embedding, torch.float32), kwargs = {})
#   %pow_1 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type, 2), kwargs = {})
#   %mean : [num_users=1] = call_function[target=torch.ops.aten.mean.dim](args = (%pow_1, [2], True), kwargs = {})
#   %add : [num_users=1] = call_function[target=torch.ops.aten.add.Scalar](args = (%mean, 0.0078125), kwargs = {})
#   %rsqrt : [num_users=1] = call_function[target=torch.ops.aten.rsqrt.default](args = (%add,), kwargs = {})
#   %mul : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type, %rsqrt), kwargs = {})
#   %convert_element_type_1 : [num_users=7] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul, torch.bfloat16), kwargs = {})
#   %add_21 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_12, %view_35), kwargs = {})
#   %add_23 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_21, %view_39), kwargs = {})
#   %mul_31 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%select_4, %add_23), kwargs = {})
#   %mul_32 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%select_5, %convert_element_type_1), kwargs = {})
#   %add_24 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_31, %mul_32), kwargs = {})
#   %convert_element_type_61 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_24, torch.float32), kwargs = {})
#   %pow_12 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_61, 2), kwargs = {})
#   %mean_9 : [num_users=1] = call_function[target=torch.ops.aten.mean.dim](args = (%pow_12, [2], True), kwargs = {})
#   %add_25 : [num_users=1] = call_function[target=torch.ops.aten.add.Scalar](args = (%mean_9, 0.0078125), kwargs = {})
#   %rsqrt_9 : [num_users=1] = call_function[target=torch.ops.aten.rsqrt.default](args = (%add_25,), kwargs = {})
#   %mul_33 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_61, %rsqrt_9), kwargs = {})
#   %convert_element_type_62 : [num_users=3] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul_33, torch.bfloat16), kwargs = {})
triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_9 = async_compile.triton('triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_9', '''
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
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*fp32', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'in_ptr3': '*fp32', 'in_ptr4': '*i64', 'in_ptr5': '*bf16', 'in_ptr6': '*fp32', 'out_ptr1': '*bf16', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_9', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': True, 'num_load': 7, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_9(in_out_ptr0, in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, in_ptr5, in_ptr6, out_ptr1, xnumel, rnumel):
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
    tmp0 = tl.load(in_ptr0 + (2))
    tmp1 = tl.broadcast_to(tmp0, [RBLOCK])
    tmp3 = tl.load(in_out_ptr0 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp4 = tl.load(in_ptr1 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp6 = tl.load(in_ptr2 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp9 = tl.load(in_ptr3 + (2))
    tmp10 = tl.broadcast_to(tmp9, [RBLOCK])
    tmp12 = tl.load(in_ptr4 + (x0), None, eviction_policy='evict_last')
    tmp20 = tl.load(in_ptr6 + (x0), None, eviction_policy='evict_last')
    tmp2 = tmp1.to(tl.float32)
    tmp5 = tmp3 + tmp4
    tmp7 = tmp5 + tmp6
    tmp8 = tmp2 * tmp7
    tmp11 = tmp10.to(tl.float32)
    tmp13 = tl.full([RBLOCK], 8192, tl.int32)
    tmp14 = tmp12 + tmp13
    tmp15 = tmp12 < 0
    tmp16 = tl.where(tmp15, tmp14, tmp12)
    tl.device_assert((0 <= tmp16) & (tmp16 < 8192), "index out of bounds: 0 <= tmp16 < 8192")
    tmp18 = tl.load(in_ptr5 + (r1 + 384*tmp16), rmask, other=0.0).to(tl.float32)
    tmp19 = tmp18.to(tl.float32)
    tmp21 = 384.0
    tmp22 = tmp20 / tmp21
    tmp23 = 0.0078125
    tmp24 = tmp22 + tmp23
    tmp25 = libdevice.rsqrt(tmp24)
    tmp26 = tmp19 * tmp25
    tmp27 = tmp26.to(tl.float32)
    tmp28 = tmp11 * tmp27
    tmp29 = tmp8 + tmp28
    tmp30 = tmp29.to(tl.float32)
    tmp31 = tmp30 * tmp30
    tmp32 = tl.broadcast_to(tmp31, [RBLOCK])
    tmp34 = tl.where(rmask, tmp32, 0)
    tmp35 = triton_helpers.promote_to_tensor(tl.sum(tmp34, 0))
    tmp36 = tmp35 / tmp21
    tmp37 = tmp36 + tmp23
    tmp38 = libdevice.rsqrt(tmp37)
    tmp39 = tmp30 * tmp38
    tmp40 = tmp39.to(tl.float32)
    tl.store(in_out_ptr0 + (r1 + 384*x0), tmp29, rmask)
    tl.store(out_ptr1 + (r1 + 384*x0), tmp40, rmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/no/cnobfygu6ryns2jzfkpxrvu5k4zwdl3ejzvu5qo2bhimpkks3kg5.py
# Topologically Sorted Source Nodes: [x, x_1, x_15, x_19, mul_32, mul_33, x_20, rms_norm_13], Original ATen: [aten.embedding, aten._to_copy, aten.pow, aten.mean, aten.add, aten.rsqrt, aten.mul]
# Source node to ATen node mapping:
#   mul_32 => mul_45
#   mul_33 => mul_46
#   rms_norm_13 => add_36, convert_element_type_89, convert_element_type_90, mean_13, mul_47, pow_17, rsqrt_13
#   x => embedding
#   x_1 => add, convert_element_type, convert_element_type_1, mean, mul, pow_1, rsqrt
#   x_15 => add_32
#   x_19 => add_34
#   x_20 => add_35
# Graph fragment:
#   %embedding : [num_users=1] = call_function[target=torch.ops.aten.embedding.default](args = (%arg3_1, %arg0_1), kwargs = {})
#   %convert_element_type : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%embedding, torch.float32), kwargs = {})
#   %pow_1 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type, 2), kwargs = {})
#   %mean : [num_users=1] = call_function[target=torch.ops.aten.mean.dim](args = (%pow_1, [2], True), kwargs = {})
#   %add : [num_users=1] = call_function[target=torch.ops.aten.add.Scalar](args = (%mean, 0.0078125), kwargs = {})
#   %rsqrt : [num_users=1] = call_function[target=torch.ops.aten.rsqrt.default](args = (%add,), kwargs = {})
#   %mul : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type, %rsqrt), kwargs = {})
#   %convert_element_type_1 : [num_users=7] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul, torch.bfloat16), kwargs = {})
#   %add_32 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_24, %view_53), kwargs = {})
#   %add_34 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_32, %view_57), kwargs = {})
#   %mul_45 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%select_6, %add_34), kwargs = {})
#   %mul_46 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%select_7, %convert_element_type_1), kwargs = {})
#   %add_35 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_45, %mul_46), kwargs = {})
#   %convert_element_type_89 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_35, torch.float32), kwargs = {})
#   %pow_17 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_89, 2), kwargs = {})
#   %mean_13 : [num_users=1] = call_function[target=torch.ops.aten.mean.dim](args = (%pow_17, [2], True), kwargs = {})
#   %add_36 : [num_users=1] = call_function[target=torch.ops.aten.add.Scalar](args = (%mean_13, 0.0078125), kwargs = {})
#   %rsqrt_13 : [num_users=1] = call_function[target=torch.ops.aten.rsqrt.default](args = (%add_36,), kwargs = {})
#   %mul_47 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_89, %rsqrt_13), kwargs = {})
#   %convert_element_type_90 : [num_users=4] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul_47, torch.bfloat16), kwargs = {})
triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_10 = async_compile.triton('triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_10', '''
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
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*fp32', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'in_ptr3': '*fp32', 'in_ptr4': '*i64', 'in_ptr5': '*bf16', 'in_ptr6': '*fp32', 'out_ptr1': '*bf16', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_10', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': True, 'num_load': 7, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_10(in_out_ptr0, in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, in_ptr5, in_ptr6, out_ptr1, xnumel, rnumel):
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
    tmp0 = tl.load(in_ptr0 + (3))
    tmp1 = tl.broadcast_to(tmp0, [RBLOCK])
    tmp3 = tl.load(in_out_ptr0 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp4 = tl.load(in_ptr1 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp6 = tl.load(in_ptr2 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp9 = tl.load(in_ptr3 + (3))
    tmp10 = tl.broadcast_to(tmp9, [RBLOCK])
    tmp12 = tl.load(in_ptr4 + (x0), None, eviction_policy='evict_last')
    tmp20 = tl.load(in_ptr6 + (x0), None, eviction_policy='evict_last')
    tmp2 = tmp1.to(tl.float32)
    tmp5 = tmp3 + tmp4
    tmp7 = tmp5 + tmp6
    tmp8 = tmp2 * tmp7
    tmp11 = tmp10.to(tl.float32)
    tmp13 = tl.full([RBLOCK], 8192, tl.int32)
    tmp14 = tmp12 + tmp13
    tmp15 = tmp12 < 0
    tmp16 = tl.where(tmp15, tmp14, tmp12)
    tl.device_assert((0 <= tmp16) & (tmp16 < 8192), "index out of bounds: 0 <= tmp16 < 8192")
    tmp18 = tl.load(in_ptr5 + (r1 + 384*tmp16), rmask, other=0.0).to(tl.float32)
    tmp19 = tmp18.to(tl.float32)
    tmp21 = 384.0
    tmp22 = tmp20 / tmp21
    tmp23 = 0.0078125
    tmp24 = tmp22 + tmp23
    tmp25 = libdevice.rsqrt(tmp24)
    tmp26 = tmp19 * tmp25
    tmp27 = tmp26.to(tl.float32)
    tmp28 = tmp11 * tmp27
    tmp29 = tmp8 + tmp28
    tmp30 = tmp29.to(tl.float32)
    tmp31 = tmp30 * tmp30
    tmp32 = tl.broadcast_to(tmp31, [RBLOCK])
    tmp34 = tl.where(rmask, tmp32, 0)
    tmp35 = triton_helpers.promote_to_tensor(tl.sum(tmp34, 0))
    tmp36 = tmp35 / tmp21
    tmp37 = tmp36 + tmp23
    tmp38 = libdevice.rsqrt(tmp37)
    tmp39 = tmp30 * tmp38
    tmp40 = tmp39.to(tl.float32)
    tl.store(in_out_ptr0 + (r1 + 384*x0), tmp29, rmask)
    tl.store(out_ptr1 + (r1 + 384*x0), tmp40, rmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/iy/ciyfrx3zlgotvpbpceqx7lgemdj27n77f4uoht4jzmobhrw2objc.py
# Topologically Sorted Source Nodes: [x, x_1, x_21, x_25, mul_44, mul_45, x_26, rms_norm_17], Original ATen: [aten.embedding, aten._to_copy, aten.pow, aten.mean, aten.add, aten.rsqrt, aten.mul]
# Source node to ATen node mapping:
#   mul_44 => mul_61
#   mul_45 => mul_62
#   rms_norm_17 => add_48, convert_element_type_120, convert_element_type_121, mean_17, mul_63, pow_22, rsqrt_17
#   x => embedding
#   x_1 => add, convert_element_type, convert_element_type_1, mean, mul, pow_1, rsqrt
#   x_21 => add_44
#   x_25 => add_46
#   x_26 => add_47
# Graph fragment:
#   %embedding : [num_users=1] = call_function[target=torch.ops.aten.embedding.default](args = (%arg3_1, %arg0_1), kwargs = {})
#   %convert_element_type : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%embedding, torch.float32), kwargs = {})
#   %pow_1 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type, 2), kwargs = {})
#   %mean : [num_users=1] = call_function[target=torch.ops.aten.mean.dim](args = (%pow_1, [2], True), kwargs = {})
#   %add : [num_users=1] = call_function[target=torch.ops.aten.add.Scalar](args = (%mean, 0.0078125), kwargs = {})
#   %rsqrt : [num_users=1] = call_function[target=torch.ops.aten.rsqrt.default](args = (%add,), kwargs = {})
#   %mul : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type, %rsqrt), kwargs = {})
#   %convert_element_type_1 : [num_users=7] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul, torch.bfloat16), kwargs = {})
#   %add_44 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_35, %view_75), kwargs = {})
#   %add_46 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_44, %view_79), kwargs = {})
#   %mul_61 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%select_8, %add_46), kwargs = {})
#   %mul_62 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%select_9, %convert_element_type_1), kwargs = {})
#   %add_47 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_61, %mul_62), kwargs = {})
#   %convert_element_type_120 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_47, torch.float32), kwargs = {})
#   %pow_22 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_120, 2), kwargs = {})
#   %mean_17 : [num_users=1] = call_function[target=torch.ops.aten.mean.dim](args = (%pow_22, [2], True), kwargs = {})
#   %add_48 : [num_users=1] = call_function[target=torch.ops.aten.add.Scalar](args = (%mean_17, 0.0078125), kwargs = {})
#   %rsqrt_17 : [num_users=1] = call_function[target=torch.ops.aten.rsqrt.default](args = (%add_48,), kwargs = {})
#   %mul_63 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_120, %rsqrt_17), kwargs = {})
#   %convert_element_type_121 : [num_users=3] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul_63, torch.bfloat16), kwargs = {})
triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_11 = async_compile.triton('triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_11', '''
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
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*fp32', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'in_ptr3': '*fp32', 'in_ptr4': '*i64', 'in_ptr5': '*bf16', 'in_ptr6': '*fp32', 'out_ptr1': '*bf16', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_11', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': True, 'num_load': 7, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_11(in_out_ptr0, in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, in_ptr5, in_ptr6, out_ptr1, xnumel, rnumel):
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
    tmp0 = tl.load(in_ptr0 + (4))
    tmp1 = tl.broadcast_to(tmp0, [RBLOCK])
    tmp3 = tl.load(in_out_ptr0 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp4 = tl.load(in_ptr1 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp6 = tl.load(in_ptr2 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp9 = tl.load(in_ptr3 + (4))
    tmp10 = tl.broadcast_to(tmp9, [RBLOCK])
    tmp12 = tl.load(in_ptr4 + (x0), None, eviction_policy='evict_last')
    tmp20 = tl.load(in_ptr6 + (x0), None, eviction_policy='evict_last')
    tmp2 = tmp1.to(tl.float32)
    tmp5 = tmp3 + tmp4
    tmp7 = tmp5 + tmp6
    tmp8 = tmp2 * tmp7
    tmp11 = tmp10.to(tl.float32)
    tmp13 = tl.full([RBLOCK], 8192, tl.int32)
    tmp14 = tmp12 + tmp13
    tmp15 = tmp12 < 0
    tmp16 = tl.where(tmp15, tmp14, tmp12)
    tl.device_assert((0 <= tmp16) & (tmp16 < 8192), "index out of bounds: 0 <= tmp16 < 8192")
    tmp18 = tl.load(in_ptr5 + (r1 + 384*tmp16), rmask, other=0.0).to(tl.float32)
    tmp19 = tmp18.to(tl.float32)
    tmp21 = 384.0
    tmp22 = tmp20 / tmp21
    tmp23 = 0.0078125
    tmp24 = tmp22 + tmp23
    tmp25 = libdevice.rsqrt(tmp24)
    tmp26 = tmp19 * tmp25
    tmp27 = tmp26.to(tl.float32)
    tmp28 = tmp11 * tmp27
    tmp29 = tmp8 + tmp28
    tmp30 = tmp29.to(tl.float32)
    tmp31 = tmp30 * tmp30
    tmp32 = tl.broadcast_to(tmp31, [RBLOCK])
    tmp34 = tl.where(rmask, tmp32, 0)
    tmp35 = triton_helpers.promote_to_tensor(tl.sum(tmp34, 0))
    tmp36 = tmp35 / tmp21
    tmp37 = tmp36 + tmp23
    tmp38 = libdevice.rsqrt(tmp37)
    tmp39 = tmp30 * tmp38
    tmp40 = tmp39.to(tl.float32)
    tl.store(in_out_ptr0 + (r1 + 384*x0), tmp29, rmask)
    tl.store(out_ptr1 + (r1 + 384*x0), tmp40, rmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/ty/ctyb327g4dullshgw2dxfnih7whqlhnalounm4oy32g6niuhavj5.py
# Topologically Sorted Source Nodes: [x, x_1, x_27, x_31, mul_54, mul_55, x_32, rms_norm_21], Original ATen: [aten.embedding, aten._to_copy, aten.pow, aten.mean, aten.add, aten.rsqrt, aten.mul]
# Source node to ATen node mapping:
#   mul_54 => mul_75
#   mul_55 => mul_76
#   rms_norm_21 => add_59, convert_element_type_148, convert_element_type_149, mean_21, mul_77, pow_27, rsqrt_21
#   x => embedding
#   x_1 => add, convert_element_type, convert_element_type_1, mean, mul, pow_1, rsqrt
#   x_27 => add_55
#   x_31 => add_57
#   x_32 => add_58
# Graph fragment:
#   %embedding : [num_users=1] = call_function[target=torch.ops.aten.embedding.default](args = (%arg3_1, %arg0_1), kwargs = {})
#   %convert_element_type : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%embedding, torch.float32), kwargs = {})
#   %pow_1 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type, 2), kwargs = {})
#   %mean : [num_users=1] = call_function[target=torch.ops.aten.mean.dim](args = (%pow_1, [2], True), kwargs = {})
#   %add : [num_users=1] = call_function[target=torch.ops.aten.add.Scalar](args = (%mean, 0.0078125), kwargs = {})
#   %rsqrt : [num_users=1] = call_function[target=torch.ops.aten.rsqrt.default](args = (%add,), kwargs = {})
#   %mul : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type, %rsqrt), kwargs = {})
#   %convert_element_type_1 : [num_users=7] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul, torch.bfloat16), kwargs = {})
#   %add_55 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_47, %view_93), kwargs = {})
#   %add_57 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_55, %view_97), kwargs = {})
#   %mul_75 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%select_10, %add_57), kwargs = {})
#   %mul_76 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%select_11, %convert_element_type_1), kwargs = {})
#   %add_58 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_75, %mul_76), kwargs = {})
#   %convert_element_type_148 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_58, torch.float32), kwargs = {})
#   %pow_27 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_148, 2), kwargs = {})
#   %mean_21 : [num_users=1] = call_function[target=torch.ops.aten.mean.dim](args = (%pow_27, [2], True), kwargs = {})
#   %add_59 : [num_users=1] = call_function[target=torch.ops.aten.add.Scalar](args = (%mean_21, 0.0078125), kwargs = {})
#   %rsqrt_21 : [num_users=1] = call_function[target=torch.ops.aten.rsqrt.default](args = (%add_59,), kwargs = {})
#   %mul_77 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_148, %rsqrt_21), kwargs = {})
#   %convert_element_type_149 : [num_users=4] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul_77, torch.bfloat16), kwargs = {})
triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_12 = async_compile.triton('triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_12', '''
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
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*fp32', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'in_ptr3': '*fp32', 'in_ptr4': '*i64', 'in_ptr5': '*bf16', 'in_ptr6': '*fp32', 'out_ptr1': '*bf16', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_12', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': True, 'num_load': 7, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_12(in_out_ptr0, in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, in_ptr5, in_ptr6, out_ptr1, xnumel, rnumel):
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
    tmp0 = tl.load(in_ptr0 + (5))
    tmp1 = tl.broadcast_to(tmp0, [RBLOCK])
    tmp3 = tl.load(in_out_ptr0 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp4 = tl.load(in_ptr1 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp6 = tl.load(in_ptr2 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp9 = tl.load(in_ptr3 + (5))
    tmp10 = tl.broadcast_to(tmp9, [RBLOCK])
    tmp12 = tl.load(in_ptr4 + (x0), None, eviction_policy='evict_last')
    tmp20 = tl.load(in_ptr6 + (x0), None, eviction_policy='evict_last')
    tmp2 = tmp1.to(tl.float32)
    tmp5 = tmp3 + tmp4
    tmp7 = tmp5 + tmp6
    tmp8 = tmp2 * tmp7
    tmp11 = tmp10.to(tl.float32)
    tmp13 = tl.full([RBLOCK], 8192, tl.int32)
    tmp14 = tmp12 + tmp13
    tmp15 = tmp12 < 0
    tmp16 = tl.where(tmp15, tmp14, tmp12)
    tl.device_assert((0 <= tmp16) & (tmp16 < 8192), "index out of bounds: 0 <= tmp16 < 8192")
    tmp18 = tl.load(in_ptr5 + (r1 + 384*tmp16), rmask, other=0.0).to(tl.float32)
    tmp19 = tmp18.to(tl.float32)
    tmp21 = 384.0
    tmp22 = tmp20 / tmp21
    tmp23 = 0.0078125
    tmp24 = tmp22 + tmp23
    tmp25 = libdevice.rsqrt(tmp24)
    tmp26 = tmp19 * tmp25
    tmp27 = tmp26.to(tl.float32)
    tmp28 = tmp11 * tmp27
    tmp29 = tmp8 + tmp28
    tmp30 = tmp29.to(tl.float32)
    tmp31 = tmp30 * tmp30
    tmp32 = tl.broadcast_to(tmp31, [RBLOCK])
    tmp34 = tl.where(rmask, tmp32, 0)
    tmp35 = triton_helpers.promote_to_tensor(tl.sum(tmp34, 0))
    tmp36 = tmp35 / tmp21
    tmp37 = tmp36 + tmp23
    tmp38 = libdevice.rsqrt(tmp37)
    tmp39 = tmp30 * tmp38
    tmp40 = tmp39.to(tl.float32)
    tl.store(in_out_ptr0 + (r1 + 384*x0), tmp29, rmask)
    tl.store(out_ptr1 + (r1 + 384*x0), tmp40, rmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/t6/ct6aa4yd2ymmj3pfwvmsfclys5zzxduq5iekgqbkzsyei67zdpd2.py
# Topologically Sorted Source Nodes: [x_33, x_37, x_38], Original ATen: [aten.add, aten._to_copy, aten.pow, aten.mean, aten.rsqrt, aten.mul]
# Source node to ATen node mapping:
#   x_33 => add_67
#   x_37 => add_69
#   x_38 => add_70, convert_element_type_179, convert_element_type_180, mean_25, mul_91, pow_32, rsqrt_25
# Graph fragment:
#   %add_67 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_58, %view_115), kwargs = {})
#   %add_69 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%add_67, %view_119), kwargs = {})
#   %convert_element_type_179 : [num_users=2] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%add_69, torch.float32), kwargs = {})
#   %pow_32 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%convert_element_type_179, 2), kwargs = {})
#   %mean_25 : [num_users=1] = call_function[target=torch.ops.aten.mean.dim](args = (%pow_32, [2], True), kwargs = {})
#   %add_70 : [num_users=1] = call_function[target=torch.ops.aten.add.Scalar](args = (%mean_25, 0.0078125), kwargs = {})
#   %rsqrt_25 : [num_users=1] = call_function[target=torch.ops.aten.rsqrt.default](args = (%add_70,), kwargs = {})
#   %mul_91 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%convert_element_type_179, %rsqrt_25), kwargs = {})
#   %convert_element_type_180 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%mul_91, torch.bfloat16), kwargs = {})
triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_13 = async_compile.triton('triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_13', '''
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
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_13', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': True, 'num_load': 3, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_13(in_out_ptr0, in_ptr0, in_ptr1, xnumel, rnumel):
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
    tmp2 = tmp0 + tmp1
    tmp4 = tmp2 + tmp3
    tmp5 = tmp4.to(tl.float32)
    tmp6 = tmp5 * tmp5
    tmp7 = tl.broadcast_to(tmp6, [RBLOCK])
    tmp9 = tl.where(rmask, tmp7, 0)
    tmp10 = triton_helpers.promote_to_tensor(tl.sum(tmp9, 0))
    tmp11 = 384.0
    tmp12 = tmp10 / tmp11
    tmp13 = 0.0078125
    tmp14 = tmp12 + tmp13
    tmp15 = libdevice.rsqrt(tmp14)
    tmp16 = tmp5 * tmp15
    tmp17 = tmp16.to(tl.float32)
    tl.store(in_out_ptr0 + (r1 + 384*x0), tmp17, rmask)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/gm/cgmrfql3fougwl6yrbrstt5wr3anqyiwk6t5kbftyhtskxis6qmc.py
# Topologically Sorted Source Nodes: [logits], Original ATen: [aten._to_copy]
# Source node to ATen node mapping:
#   logits => convert_element_type_181
# Graph fragment:
#   %convert_element_type_181 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%arg48_1, torch.bfloat16), kwargs = {})
triton_poi_fused__to_copy_14 = async_compile.triton('triton_poi_fused__to_copy_14', '''
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
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused__to_copy_14', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 1, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused__to_copy_14(in_ptr0, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 3145728
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (x0), None)
    tmp1 = tmp0.to(tl.float32)
    tl.store(out_ptr0 + (x0), tmp1, None)
''', device_str='cuda')


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_edits/E2/work/.ar_cache/inductor/lw/clwzw2snm32conorhp4gnm5lqji2yn2aaoaegv53cnakazimpuhe.py
# Topologically Sorted Source Nodes: [logits_1, truediv, tanh, logits_2], Original ATen: [aten._to_copy, aten.div, aten.tanh, aten.mul]
# Source node to ATen node mapping:
#   logits_1 => convert_element_type_184
#   logits_2 => mul_92
#   tanh => tanh
#   truediv => div
# Graph fragment:
#   %convert_element_type_184 : [num_users=1] = call_function[target=torch.ops.prims.convert_element_type.default](args = (%view_121, torch.float32), kwargs = {})
#   %div : [num_users=1] = call_function[target=torch.ops.aten.div.Tensor](args = (%convert_element_type_184, 15), kwargs = {})
#   %tanh : [num_users=1] = call_function[target=torch.ops.aten.tanh.default](args = (%div,), kwargs = {})
#   %mul_92 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%tanh, 15), kwargs = {})
triton_poi_fused__to_copy_div_mul_tanh_15 = async_compile.triton('triton_poi_fused__to_copy_div_mul_tanh_15', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.pointwise(
    size_hints={'x': 268435456}, 
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*bf16', 'out_ptr0': '*fp32', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused__to_copy_div_mul_tanh_15', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 1, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused__to_copy_div_mul_tanh_15(in_ptr0, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 268435456
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (x0), None).to(tl.float32)
    tmp1 = tmp0.to(tl.float32)
    tmp2 = 0.06666666666666667
    tmp3 = tmp1 * tmp2
    tmp4 = libdevice.tanh(tmp3)
    tmp5 = 15.0
    tmp6 = tmp4 * tmp5
    tl.store(out_ptr0 + (x0), tmp6, None)
''', device_str='cuda')


async_compile.wait(globals())
del async_compile

def call(args):
    arg0_1, arg1_1, arg2_1, arg3_1, arg4_1, arg5_1, arg6_1, arg7_1, arg8_1, arg9_1, arg10_1, arg11_1, arg12_1, arg13_1, arg14_1, arg15_1, arg16_1, arg17_1, arg18_1, arg19_1, arg20_1, arg21_1, arg22_1, arg23_1, arg24_1, arg25_1, arg26_1, arg27_1, arg28_1, arg29_1, arg30_1, arg31_1, arg32_1, arg33_1, arg34_1, arg35_1, arg36_1, arg37_1, arg38_1, arg39_1, arg40_1, arg41_1, arg42_1, arg43_1, arg44_1, arg45_1, arg46_1, arg47_1, arg48_1 = args
    args.clear()
    assert_size_stride(arg0_1, (16, 2048), (2048, 1))
    assert_size_stride(arg1_1, (1, 20480, 1, 64), (1310720, 64, 64, 1))
    assert_size_stride(arg2_1, (1, 20480, 1, 64), (1310720, 64, 64, 1))
    assert_size_stride(arg3_1, (8192, 384), (384, 1))
    assert_size_stride(arg4_1, (6, ), (1, ))
    assert_size_stride(arg5_1, (6, ), (1, ))
    assert_size_stride(arg6_1, (384, 384), (384, 1))
    assert_size_stride(arg7_1, (384, 384), (384, 1))
    assert_size_stride(arg8_1, (384, 384), (384, 1))
    assert_size_stride(arg9_1, (384, 384), (384, 1))
    assert_size_stride(arg10_1, (1536, 384), (384, 1))
    assert_size_stride(arg11_1, (384, 1536), (1536, 1))
    assert_size_stride(arg12_1, (8192, 384), (384, 1))
    assert_size_stride(arg13_1, (384, 384), (384, 1))
    assert_size_stride(arg14_1, (384, 384), (384, 1))
    assert_size_stride(arg15_1, (384, 384), (384, 1))
    assert_size_stride(arg16_1, (3, 32), (32, 1))
    assert_size_stride(arg17_1, (384, 384), (384, 1))
    assert_size_stride(arg18_1, (1536, 384), (384, 1))
    assert_size_stride(arg19_1, (384, 1536), (1536, 1))
    assert_size_stride(arg20_1, (384, 384), (384, 1))
    assert_size_stride(arg21_1, (384, 384), (384, 1))
    assert_size_stride(arg22_1, (384, 384), (384, 1))
    assert_size_stride(arg23_1, (384, 384), (384, 1))
    assert_size_stride(arg24_1, (1536, 384), (384, 1))
    assert_size_stride(arg25_1, (384, 1536), (1536, 1))
    assert_size_stride(arg26_1, (8192, 384), (384, 1))
    assert_size_stride(arg27_1, (384, 384), (384, 1))
    assert_size_stride(arg28_1, (384, 384), (384, 1))
    assert_size_stride(arg29_1, (384, 384), (384, 1))
    assert_size_stride(arg30_1, (3, 32), (32, 1))
    assert_size_stride(arg31_1, (384, 384), (384, 1))
    assert_size_stride(arg32_1, (1536, 384), (384, 1))
    assert_size_stride(arg33_1, (384, 1536), (1536, 1))
    assert_size_stride(arg34_1, (384, 384), (384, 1))
    assert_size_stride(arg35_1, (384, 384), (384, 1))
    assert_size_stride(arg36_1, (384, 384), (384, 1))
    assert_size_stride(arg37_1, (384, 384), (384, 1))
    assert_size_stride(arg38_1, (1536, 384), (384, 1))
    assert_size_stride(arg39_1, (384, 1536), (1536, 1))
    assert_size_stride(arg40_1, (8192, 384), (384, 1))
    assert_size_stride(arg41_1, (384, 384), (384, 1))
    assert_size_stride(arg42_1, (384, 384), (384, 1))
    assert_size_stride(arg43_1, (384, 384), (384, 1))
    assert_size_stride(arg44_1, (3, 32), (32, 1))
    assert_size_stride(arg45_1, (384, 384), (384, 1))
    assert_size_stride(arg46_1, (1536, 384), (384, 1))
    assert_size_stride(arg47_1, (384, 1536), (1536, 1))
    assert_size_stride(arg48_1, (8192, 384), (384, 1))
    with torch.cuda._DeviceGuard(0):
        torch.cuda.set_device(0)
        buf0 = empty_strided_cuda((16, 2048, 1), (2048, 1, 32768), torch.float32)
        buf1 = empty_strided_cuda((16, 2048, 384), (786432, 384, 1), torch.bfloat16)
        buf3 = empty_strided_cuda((16, 2048, 384), (786432, 384, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [x, x_1, mul, mul_1, x_2, rms_norm_1], Original ATen: [aten.embedding, aten._to_copy, aten.pow, aten.mean, aten.add, aten.rsqrt, aten.mul]
        stream0 = get_raw_stream(0)
        triton_red_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_0.run(arg0_1, arg3_1, arg4_1, arg5_1, buf0, buf1, buf3, 32768, 384, grid=grid(32768), stream=stream0)
        buf4 = empty_strided_cuda((384, 384), (384, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_1.run(arg6_1, buf4, 147456, grid=grid(147456), stream=stream0)
        del arg6_1
        buf5 = empty_strided_cuda((32768, 384), (384, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf3, (32768, 384), (384, 1), 0), reinterpret_tensor(buf4, (384, 384), (1, 384), 0), out=buf5)
        buf8 = buf4; del buf4  # reuse
        # Topologically Sorted Source Nodes: [linear_1], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_1.run(arg7_1, buf8, 147456, grid=grid(147456), stream=stream0)
        del arg7_1
        buf9 = empty_strided_cuda((32768, 384), (384, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear_1], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf3, (32768, 384), (384, 1), 0), reinterpret_tensor(buf8, (384, 384), (1, 384), 0), out=buf9)
        buf14 = empty_strided_cuda((16, 3, 2048, 128), (786432, 128, 384, 1), torch.bfloat16)
        buf15 = empty_strided_cuda((16, 3, 2048, 128), (786432, 128, 384, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [q_1, q_2, k_1, k_2, y], Original ATen: [aten.cat, aten._to_copy, aten.pow, aten.mean, aten._scaled_dot_product_flash_attention]
        stream0 = get_raw_stream(0)
        triton_per_fused__scaled_dot_product_flash_attention__to_copy_cat_mean_pow_2.run(buf5, arg1_1, arg2_1, buf9, buf14, buf15, 98304, 128, grid=grid(98304), stream=stream0)
        del buf5
        buf12 = buf8; del buf8  # reuse
        # Topologically Sorted Source Nodes: [linear_2], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_1.run(arg8_1, buf12, 147456, grid=grid(147456), stream=stream0)
        del arg8_1
        buf13 = buf9; del buf9  # reuse
        # Topologically Sorted Source Nodes: [linear_2], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf3, (32768, 384), (384, 1), 0), reinterpret_tensor(buf12, (384, 384), (1, 384), 0), out=buf13)
        # Topologically Sorted Source Nodes: [y], Original ATen: [aten._scaled_dot_product_flash_attention]
        buf16 = torch.ops.aten._scaled_dot_product_flash_attention.default(buf14, buf15, reinterpret_tensor(buf13, (16, 3, 2048, 128), (786432, 128, 384, 1), 0), 0.0, True, scale=0.08838834764831843)
        buf17 = buf16[0]
        del buf16
        buf22 = buf12; del buf12  # reuse
        # Topologically Sorted Source Nodes: [y_2], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_1.run(arg9_1, buf22, 147456, grid=grid(147456), stream=stream0)
        del arg9_1
        buf23 = reinterpret_tensor(buf15, (32768, 384), (384, 1), 0); del buf15  # reuse
        # Topologically Sorted Source Nodes: [y_2], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf17, (32768, 384), (384, 1), 0), reinterpret_tensor(buf22, (384, 384), (1, 384), 0), out=buf23)
        buf25 = reinterpret_tensor(buf17, (16, 2048, 384), (786432, 384, 1), 0); del buf17  # reuse
        # Topologically Sorted Source Nodes: [x_3, rms_norm_4], Original ATen: [aten.add, aten._to_copy, aten.pow, aten.mean, aten.rsqrt, aten.mul]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_3.run(buf1, buf23, buf25, 32768, 384, grid=grid(32768), stream=stream0)
        buf26 = empty_strided_cuda((1536, 384), (384, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [x_4], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_4.run(arg10_1, buf26, 589824, grid=grid(589824), stream=stream0)
        del arg10_1
        buf27 = empty_strided_cuda((32768, 1536), (1536, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [x_4], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf25, (32768, 384), (384, 1), 0), reinterpret_tensor(buf26, (384, 1536), (1, 384), 0), out=buf27)
        buf28 = reinterpret_tensor(buf27, (16, 2048, 1536), (3145728, 1536, 1), 0); del buf27  # reuse
        # Topologically Sorted Source Nodes: [relu, x_5, x_6], Original ATen: [aten.relu, aten._to_copy, aten.pow]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_pow_relu_5.run(buf28, 50331648, grid=grid(50331648), stream=stream0)
        buf29 = reinterpret_tensor(buf26, (384, 1536), (1536, 1), 0); del buf26  # reuse
        # Topologically Sorted Source Nodes: [x_6], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_4.run(arg11_1, buf29, 589824, grid=grid(589824), stream=stream0)
        del arg11_1
        buf30 = reinterpret_tensor(buf25, (32768, 384), (384, 1), 0); del buf25  # reuse
        # Topologically Sorted Source Nodes: [x_6], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf28, (32768, 1536), (1536, 1), 0), reinterpret_tensor(buf29, (1536, 384), (1, 1536), 0), out=buf30)
        buf31 = buf1; del buf1  # reuse
        buf33 = reinterpret_tensor(buf14, (16, 2048, 384), (786432, 384, 1), 0); del buf14  # reuse
        # Topologically Sorted Source Nodes: [x, x_1, x_3, x_7, mul_10, mul_11, x_8, rms_norm_5], Original ATen: [aten.embedding, aten._to_copy, aten.pow, aten.mean, aten.add, aten.rsqrt, aten.mul]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_6.run(buf31, arg4_1, buf23, buf30, arg5_1, arg0_1, arg3_1, buf0, buf33, 32768, 384, grid=grid(32768), stream=stream0)
        buf34 = buf22; del buf22  # reuse
        # Topologically Sorted Source Nodes: [linear_6], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_1.run(arg13_1, buf34, 147456, grid=grid(147456), stream=stream0)
        del arg13_1
        buf35 = buf30; del buf30  # reuse
        # Topologically Sorted Source Nodes: [linear_6], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf33, (32768, 384), (384, 1), 0), reinterpret_tensor(buf34, (384, 384), (1, 384), 0), out=buf35)
        buf38 = buf34; del buf34  # reuse
        # Topologically Sorted Source Nodes: [linear_7], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_1.run(arg14_1, buf38, 147456, grid=grid(147456), stream=stream0)
        del arg14_1
        buf39 = buf23; del buf23  # reuse
        # Topologically Sorted Source Nodes: [linear_7], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf33, (32768, 384), (384, 1), 0), reinterpret_tensor(buf38, (384, 384), (1, 384), 0), out=buf39)
        buf46 = reinterpret_tensor(buf13, (16, 3, 2048, 128), (786432, 128, 384, 1), 0); del buf13  # reuse
        buf47 = reinterpret_tensor(buf3, (16, 3, 2048, 128), (786432, 128, 384, 1), 0); del buf3  # reuse
        # Topologically Sorted Source Nodes: [q_5, q_6, k_6, k_7, y_3], Original ATen: [aten.cat, aten._to_copy, aten.pow, aten.mean, aten._scaled_dot_product_flash_attention]
        stream0 = get_raw_stream(0)
        triton_per_fused__scaled_dot_product_flash_attention__to_copy_cat_mean_pow_2.run(buf35, arg1_1, arg2_1, buf39, buf46, buf47, 98304, 128, grid=grid(98304), stream=stream0)
        del buf35
        buf42 = buf38; del buf38  # reuse
        # Topologically Sorted Source Nodes: [linear_8], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_1.run(arg15_1, buf42, 147456, grid=grid(147456), stream=stream0)
        del arg15_1
        buf43 = buf39; del buf39  # reuse
        # Topologically Sorted Source Nodes: [linear_8], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf33, (32768, 384), (384, 1), 0), reinterpret_tensor(buf42, (384, 384), (1, 384), 0), out=buf43)
        buf44 = empty_strided_cuda((3, 32), (32, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear_9], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_7.run(arg16_1, buf44, 96, grid=grid(96), stream=stream0)
        del arg16_1
        buf45 = empty_strided_cuda((16, 2048, 3), (6144, 3, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [linear_9], Original ATen: [aten.bmm]
        extern_kernels.bmm(reinterpret_tensor(buf33, (16, 2048, 32), (786432, 384, 1), 0), reinterpret_tensor(buf44, (16, 32, 3), (0, 1, 32), 0), out=buf45)
        buf48 = reinterpret_tensor(buf43, (16, 3, 2048, 128), (786432, 128, 384, 1), 0); del buf43  # reuse
        # Topologically Sorted Source Nodes: [y_3], Original ATen: [aten._scaled_dot_product_flash_attention]
        stream0 = get_raw_stream(0)
        triton_poi_fused__scaled_dot_product_flash_attention_8.run(buf48, buf45, arg0_1, arg12_1, 12582912, grid=grid(12582912), stream=stream0)
        del arg12_1
        # Topologically Sorted Source Nodes: [y_3], Original ATen: [aten._scaled_dot_product_flash_attention]
        buf49 = torch.ops.aten._scaled_dot_product_flash_attention.default(buf46, buf47, buf48, 0.0, True, scale=0.08838834764831843)
        buf50 = buf49[0]
        del buf49
        buf55 = buf42; del buf42  # reuse
        # Topologically Sorted Source Nodes: [y_5], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_1.run(arg17_1, buf55, 147456, grid=grid(147456), stream=stream0)
        del arg17_1
        buf56 = reinterpret_tensor(buf48, (32768, 384), (384, 1), 0); del buf48  # reuse
        # Topologically Sorted Source Nodes: [y_5], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf50, (32768, 384), (384, 1), 0), reinterpret_tensor(buf55, (384, 384), (1, 384), 0), out=buf56)
        buf58 = reinterpret_tensor(buf50, (16, 2048, 384), (786432, 384, 1), 0); del buf50  # reuse
        # Topologically Sorted Source Nodes: [x_9, rms_norm_8], Original ATen: [aten.add, aten._to_copy, aten.pow, aten.mean, aten.rsqrt, aten.mul]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_3.run(buf31, buf56, buf58, 32768, 384, grid=grid(32768), stream=stream0)
        buf59 = reinterpret_tensor(buf29, (1536, 384), (384, 1), 0); del buf29  # reuse
        # Topologically Sorted Source Nodes: [x_10], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_4.run(arg18_1, buf59, 589824, grid=grid(589824), stream=stream0)
        del arg18_1
        buf60 = reinterpret_tensor(buf28, (32768, 1536), (1536, 1), 0); del buf28  # reuse
        # Topologically Sorted Source Nodes: [x_10], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf58, (32768, 384), (384, 1), 0), reinterpret_tensor(buf59, (384, 1536), (1, 384), 0), out=buf60)
        buf61 = reinterpret_tensor(buf60, (16, 2048, 1536), (3145728, 1536, 1), 0); del buf60  # reuse
        # Topologically Sorted Source Nodes: [relu_1, x_11, x_12], Original ATen: [aten.relu, aten._to_copy, aten.pow]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_pow_relu_5.run(buf61, 50331648, grid=grid(50331648), stream=stream0)
        buf62 = reinterpret_tensor(buf59, (384, 1536), (1536, 1), 0); del buf59  # reuse
        # Topologically Sorted Source Nodes: [x_12], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_4.run(arg19_1, buf62, 589824, grid=grid(589824), stream=stream0)
        del arg19_1
        buf63 = reinterpret_tensor(buf58, (32768, 384), (384, 1), 0); del buf58  # reuse
        # Topologically Sorted Source Nodes: [x_12], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf61, (32768, 1536), (1536, 1), 0), reinterpret_tensor(buf62, (1536, 384), (1, 1536), 0), out=buf63)
        buf64 = buf31; del buf31  # reuse
        buf66 = reinterpret_tensor(buf47, (16, 2048, 384), (786432, 384, 1), 0); del buf47  # reuse
        # Topologically Sorted Source Nodes: [x, x_1, x_9, x_13, mul_22, mul_23, x_14, rms_norm_9], Original ATen: [aten.embedding, aten._to_copy, aten.pow, aten.mean, aten.add, aten.rsqrt, aten.mul]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_9.run(buf64, arg4_1, buf56, buf63, arg5_1, arg0_1, arg3_1, buf0, buf66, 32768, 384, grid=grid(32768), stream=stream0)
        buf67 = buf55; del buf55  # reuse
        # Topologically Sorted Source Nodes: [linear_13], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_1.run(arg20_1, buf67, 147456, grid=grid(147456), stream=stream0)
        del arg20_1
        buf68 = buf63; del buf63  # reuse
        # Topologically Sorted Source Nodes: [linear_13], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf66, (32768, 384), (384, 1), 0), reinterpret_tensor(buf67, (384, 384), (1, 384), 0), out=buf68)
        buf71 = buf67; del buf67  # reuse
        # Topologically Sorted Source Nodes: [linear_14], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_1.run(arg21_1, buf71, 147456, grid=grid(147456), stream=stream0)
        del arg21_1
        buf72 = buf56; del buf56  # reuse
        # Topologically Sorted Source Nodes: [linear_14], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf66, (32768, 384), (384, 1), 0), reinterpret_tensor(buf71, (384, 384), (1, 384), 0), out=buf72)
        buf77 = buf46; del buf46  # reuse
        buf78 = reinterpret_tensor(buf33, (16, 3, 2048, 128), (786432, 128, 384, 1), 0); del buf33  # reuse
        # Topologically Sorted Source Nodes: [q_9, q_10, k_11, k_12, y_6], Original ATen: [aten.cat, aten._to_copy, aten.pow, aten.mean, aten._scaled_dot_product_flash_attention]
        stream0 = get_raw_stream(0)
        triton_per_fused__scaled_dot_product_flash_attention__to_copy_cat_mean_pow_2.run(buf68, arg1_1, arg2_1, buf72, buf77, buf78, 98304, 128, grid=grid(98304), stream=stream0)
        del buf68
        buf75 = buf71; del buf71  # reuse
        # Topologically Sorted Source Nodes: [linear_15], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_1.run(arg22_1, buf75, 147456, grid=grid(147456), stream=stream0)
        del arg22_1
        buf76 = buf72; del buf72  # reuse
        # Topologically Sorted Source Nodes: [linear_15], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf66, (32768, 384), (384, 1), 0), reinterpret_tensor(buf75, (384, 384), (1, 384), 0), out=buf76)
        # Topologically Sorted Source Nodes: [y_6], Original ATen: [aten._scaled_dot_product_flash_attention]
        buf79 = torch.ops.aten._scaled_dot_product_flash_attention.default(buf77, buf78, reinterpret_tensor(buf76, (16, 3, 2048, 128), (786432, 128, 384, 1), 0), 0.0, True, scale=0.08838834764831843)
        buf80 = buf79[0]
        del buf79
        buf85 = buf75; del buf75  # reuse
        # Topologically Sorted Source Nodes: [y_8], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_1.run(arg23_1, buf85, 147456, grid=grid(147456), stream=stream0)
        del arg23_1
        buf86 = reinterpret_tensor(buf78, (32768, 384), (384, 1), 0); del buf78  # reuse
        # Topologically Sorted Source Nodes: [y_8], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf80, (32768, 384), (384, 1), 0), reinterpret_tensor(buf85, (384, 384), (1, 384), 0), out=buf86)
        buf88 = reinterpret_tensor(buf80, (16, 2048, 384), (786432, 384, 1), 0); del buf80  # reuse
        # Topologically Sorted Source Nodes: [x_15, rms_norm_12], Original ATen: [aten.add, aten._to_copy, aten.pow, aten.mean, aten.rsqrt, aten.mul]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_3.run(buf64, buf86, buf88, 32768, 384, grid=grid(32768), stream=stream0)
        buf89 = reinterpret_tensor(buf62, (1536, 384), (384, 1), 0); del buf62  # reuse
        # Topologically Sorted Source Nodes: [x_16], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_4.run(arg24_1, buf89, 589824, grid=grid(589824), stream=stream0)
        del arg24_1
        buf90 = reinterpret_tensor(buf61, (32768, 1536), (1536, 1), 0); del buf61  # reuse
        # Topologically Sorted Source Nodes: [x_16], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf88, (32768, 384), (384, 1), 0), reinterpret_tensor(buf89, (384, 1536), (1, 384), 0), out=buf90)
        buf91 = reinterpret_tensor(buf90, (16, 2048, 1536), (3145728, 1536, 1), 0); del buf90  # reuse
        # Topologically Sorted Source Nodes: [relu_2, x_17, x_18], Original ATen: [aten.relu, aten._to_copy, aten.pow]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_pow_relu_5.run(buf91, 50331648, grid=grid(50331648), stream=stream0)
        buf92 = reinterpret_tensor(buf89, (384, 1536), (1536, 1), 0); del buf89  # reuse
        # Topologically Sorted Source Nodes: [x_18], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_4.run(arg25_1, buf92, 589824, grid=grid(589824), stream=stream0)
        del arg25_1
        buf93 = reinterpret_tensor(buf88, (32768, 384), (384, 1), 0); del buf88  # reuse
        # Topologically Sorted Source Nodes: [x_18], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf91, (32768, 1536), (1536, 1), 0), reinterpret_tensor(buf92, (1536, 384), (1, 1536), 0), out=buf93)
        buf94 = buf64; del buf64  # reuse
        buf96 = reinterpret_tensor(buf77, (16, 2048, 384), (786432, 384, 1), 0); del buf77  # reuse
        # Topologically Sorted Source Nodes: [x, x_1, x_15, x_19, mul_32, mul_33, x_20, rms_norm_13], Original ATen: [aten.embedding, aten._to_copy, aten.pow, aten.mean, aten.add, aten.rsqrt, aten.mul]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_10.run(buf94, arg4_1, buf86, buf93, arg5_1, arg0_1, arg3_1, buf0, buf96, 32768, 384, grid=grid(32768), stream=stream0)
        buf97 = buf85; del buf85  # reuse
        # Topologically Sorted Source Nodes: [linear_19], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_1.run(arg27_1, buf97, 147456, grid=grid(147456), stream=stream0)
        del arg27_1
        buf98 = buf93; del buf93  # reuse
        # Topologically Sorted Source Nodes: [linear_19], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf96, (32768, 384), (384, 1), 0), reinterpret_tensor(buf97, (384, 384), (1, 384), 0), out=buf98)
        buf101 = buf97; del buf97  # reuse
        # Topologically Sorted Source Nodes: [linear_20], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_1.run(arg28_1, buf101, 147456, grid=grid(147456), stream=stream0)
        del arg28_1
        buf102 = buf86; del buf86  # reuse
        # Topologically Sorted Source Nodes: [linear_20], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf96, (32768, 384), (384, 1), 0), reinterpret_tensor(buf101, (384, 384), (1, 384), 0), out=buf102)
        buf109 = reinterpret_tensor(buf76, (16, 3, 2048, 128), (786432, 128, 384, 1), 0); del buf76  # reuse
        buf110 = reinterpret_tensor(buf66, (16, 3, 2048, 128), (786432, 128, 384, 1), 0); del buf66  # reuse
        # Topologically Sorted Source Nodes: [q_13, q_14, k_16, k_17, y_9], Original ATen: [aten.cat, aten._to_copy, aten.pow, aten.mean, aten._scaled_dot_product_flash_attention]
        stream0 = get_raw_stream(0)
        triton_per_fused__scaled_dot_product_flash_attention__to_copy_cat_mean_pow_2.run(buf98, arg1_1, arg2_1, buf102, buf109, buf110, 98304, 128, grid=grid(98304), stream=stream0)
        del buf102
        buf105 = buf101; del buf101  # reuse
        # Topologically Sorted Source Nodes: [linear_21], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_1.run(arg29_1, buf105, 147456, grid=grid(147456), stream=stream0)
        del arg29_1
        buf106 = buf98; del buf98  # reuse
        # Topologically Sorted Source Nodes: [linear_21], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf96, (32768, 384), (384, 1), 0), reinterpret_tensor(buf105, (384, 384), (1, 384), 0), out=buf106)
        buf107 = buf44; del buf44  # reuse
        # Topologically Sorted Source Nodes: [linear_22], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_7.run(arg30_1, buf107, 96, grid=grid(96), stream=stream0)
        del arg30_1
        buf108 = buf45; del buf45  # reuse
        # Topologically Sorted Source Nodes: [linear_22], Original ATen: [aten.bmm]
        extern_kernels.bmm(reinterpret_tensor(buf96, (16, 2048, 32), (786432, 384, 1), 0), reinterpret_tensor(buf107, (16, 32, 3), (0, 1, 32), 0), out=buf108)
        buf111 = reinterpret_tensor(buf106, (16, 3, 2048, 128), (786432, 128, 384, 1), 0); del buf106  # reuse
        # Topologically Sorted Source Nodes: [y_9], Original ATen: [aten._scaled_dot_product_flash_attention]
        stream0 = get_raw_stream(0)
        triton_poi_fused__scaled_dot_product_flash_attention_8.run(buf111, buf108, arg0_1, arg26_1, 12582912, grid=grid(12582912), stream=stream0)
        del arg26_1
        # Topologically Sorted Source Nodes: [y_9], Original ATen: [aten._scaled_dot_product_flash_attention]
        buf112 = torch.ops.aten._scaled_dot_product_flash_attention.default(buf109, buf110, buf111, 0.0, True, scale=0.08838834764831843)
        buf113 = buf112[0]
        del buf112
        buf118 = buf105; del buf105  # reuse
        # Topologically Sorted Source Nodes: [y_11], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_1.run(arg31_1, buf118, 147456, grid=grid(147456), stream=stream0)
        del arg31_1
        buf119 = reinterpret_tensor(buf111, (32768, 384), (384, 1), 0); del buf111  # reuse
        # Topologically Sorted Source Nodes: [y_11], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf113, (32768, 384), (384, 1), 0), reinterpret_tensor(buf118, (384, 384), (1, 384), 0), out=buf119)
        buf121 = reinterpret_tensor(buf113, (16, 2048, 384), (786432, 384, 1), 0); del buf113  # reuse
        # Topologically Sorted Source Nodes: [x_21, rms_norm_16], Original ATen: [aten.add, aten._to_copy, aten.pow, aten.mean, aten.rsqrt, aten.mul]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_3.run(buf94, buf119, buf121, 32768, 384, grid=grid(32768), stream=stream0)
        buf122 = reinterpret_tensor(buf92, (1536, 384), (384, 1), 0); del buf92  # reuse
        # Topologically Sorted Source Nodes: [x_22], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_4.run(arg32_1, buf122, 589824, grid=grid(589824), stream=stream0)
        del arg32_1
        buf123 = reinterpret_tensor(buf91, (32768, 1536), (1536, 1), 0); del buf91  # reuse
        # Topologically Sorted Source Nodes: [x_22], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf121, (32768, 384), (384, 1), 0), reinterpret_tensor(buf122, (384, 1536), (1, 384), 0), out=buf123)
        buf124 = reinterpret_tensor(buf123, (16, 2048, 1536), (3145728, 1536, 1), 0); del buf123  # reuse
        # Topologically Sorted Source Nodes: [relu_3, x_23, x_24], Original ATen: [aten.relu, aten._to_copy, aten.pow]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_pow_relu_5.run(buf124, 50331648, grid=grid(50331648), stream=stream0)
        buf125 = reinterpret_tensor(buf122, (384, 1536), (1536, 1), 0); del buf122  # reuse
        # Topologically Sorted Source Nodes: [x_24], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_4.run(arg33_1, buf125, 589824, grid=grid(589824), stream=stream0)
        del arg33_1
        buf126 = reinterpret_tensor(buf121, (32768, 384), (384, 1), 0); del buf121  # reuse
        # Topologically Sorted Source Nodes: [x_24], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf124, (32768, 1536), (1536, 1), 0), reinterpret_tensor(buf125, (1536, 384), (1, 1536), 0), out=buf126)
        buf127 = buf94; del buf94  # reuse
        buf129 = reinterpret_tensor(buf110, (16, 2048, 384), (786432, 384, 1), 0); del buf110  # reuse
        # Topologically Sorted Source Nodes: [x, x_1, x_21, x_25, mul_44, mul_45, x_26, rms_norm_17], Original ATen: [aten.embedding, aten._to_copy, aten.pow, aten.mean, aten.add, aten.rsqrt, aten.mul]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_11.run(buf127, arg4_1, buf119, buf126, arg5_1, arg0_1, arg3_1, buf0, buf129, 32768, 384, grid=grid(32768), stream=stream0)
        buf130 = buf118; del buf118  # reuse
        # Topologically Sorted Source Nodes: [linear_26], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_1.run(arg34_1, buf130, 147456, grid=grid(147456), stream=stream0)
        del arg34_1
        buf131 = buf126; del buf126  # reuse
        # Topologically Sorted Source Nodes: [linear_26], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf129, (32768, 384), (384, 1), 0), reinterpret_tensor(buf130, (384, 384), (1, 384), 0), out=buf131)
        buf134 = buf130; del buf130  # reuse
        # Topologically Sorted Source Nodes: [linear_27], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_1.run(arg35_1, buf134, 147456, grid=grid(147456), stream=stream0)
        del arg35_1
        buf135 = buf119; del buf119  # reuse
        # Topologically Sorted Source Nodes: [linear_27], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf129, (32768, 384), (384, 1), 0), reinterpret_tensor(buf134, (384, 384), (1, 384), 0), out=buf135)
        buf140 = buf109; del buf109  # reuse
        buf141 = reinterpret_tensor(buf96, (16, 3, 2048, 128), (786432, 128, 384, 1), 0); del buf96  # reuse
        # Topologically Sorted Source Nodes: [q_17, q_18, k_21, k_22, y_12], Original ATen: [aten.cat, aten._to_copy, aten.pow, aten.mean, aten._scaled_dot_product_flash_attention]
        stream0 = get_raw_stream(0)
        triton_per_fused__scaled_dot_product_flash_attention__to_copy_cat_mean_pow_2.run(buf131, arg1_1, arg2_1, buf135, buf140, buf141, 98304, 128, grid=grid(98304), stream=stream0)
        del buf131
        buf138 = buf134; del buf134  # reuse
        # Topologically Sorted Source Nodes: [linear_28], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_1.run(arg36_1, buf138, 147456, grid=grid(147456), stream=stream0)
        del arg36_1
        buf139 = buf135; del buf135  # reuse
        # Topologically Sorted Source Nodes: [linear_28], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf129, (32768, 384), (384, 1), 0), reinterpret_tensor(buf138, (384, 384), (1, 384), 0), out=buf139)
        # Topologically Sorted Source Nodes: [y_12], Original ATen: [aten._scaled_dot_product_flash_attention]
        buf142 = torch.ops.aten._scaled_dot_product_flash_attention.default(buf140, buf141, reinterpret_tensor(buf139, (16, 3, 2048, 128), (786432, 128, 384, 1), 0), 0.0, True, scale=0.08838834764831843)
        buf143 = buf142[0]
        del buf142
        buf148 = buf138; del buf138  # reuse
        # Topologically Sorted Source Nodes: [y_14], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_1.run(arg37_1, buf148, 147456, grid=grid(147456), stream=stream0)
        del arg37_1
        buf149 = reinterpret_tensor(buf141, (32768, 384), (384, 1), 0); del buf141  # reuse
        # Topologically Sorted Source Nodes: [y_14], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf143, (32768, 384), (384, 1), 0), reinterpret_tensor(buf148, (384, 384), (1, 384), 0), out=buf149)
        buf151 = reinterpret_tensor(buf143, (16, 2048, 384), (786432, 384, 1), 0); del buf143  # reuse
        # Topologically Sorted Source Nodes: [x_27, rms_norm_20], Original ATen: [aten.add, aten._to_copy, aten.pow, aten.mean, aten.rsqrt, aten.mul]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_3.run(buf127, buf149, buf151, 32768, 384, grid=grid(32768), stream=stream0)
        buf152 = reinterpret_tensor(buf125, (1536, 384), (384, 1), 0); del buf125  # reuse
        # Topologically Sorted Source Nodes: [x_28], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_4.run(arg38_1, buf152, 589824, grid=grid(589824), stream=stream0)
        del arg38_1
        buf153 = reinterpret_tensor(buf124, (32768, 1536), (1536, 1), 0); del buf124  # reuse
        # Topologically Sorted Source Nodes: [x_28], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf151, (32768, 384), (384, 1), 0), reinterpret_tensor(buf152, (384, 1536), (1, 384), 0), out=buf153)
        buf154 = reinterpret_tensor(buf153, (16, 2048, 1536), (3145728, 1536, 1), 0); del buf153  # reuse
        # Topologically Sorted Source Nodes: [relu_4, x_29, x_30], Original ATen: [aten.relu, aten._to_copy, aten.pow]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_pow_relu_5.run(buf154, 50331648, grid=grid(50331648), stream=stream0)
        buf155 = reinterpret_tensor(buf152, (384, 1536), (1536, 1), 0); del buf152  # reuse
        # Topologically Sorted Source Nodes: [x_30], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_4.run(arg39_1, buf155, 589824, grid=grid(589824), stream=stream0)
        del arg39_1
        buf156 = reinterpret_tensor(buf151, (32768, 384), (384, 1), 0); del buf151  # reuse
        # Topologically Sorted Source Nodes: [x_30], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf154, (32768, 1536), (1536, 1), 0), reinterpret_tensor(buf155, (1536, 384), (1, 1536), 0), out=buf156)
        buf157 = buf127; del buf127  # reuse
        buf159 = reinterpret_tensor(buf140, (16, 2048, 384), (786432, 384, 1), 0); del buf140  # reuse
        # Topologically Sorted Source Nodes: [x, x_1, x_27, x_31, mul_54, mul_55, x_32, rms_norm_21], Original ATen: [aten.embedding, aten._to_copy, aten.pow, aten.mean, aten.add, aten.rsqrt, aten.mul]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_12.run(buf157, arg4_1, buf149, buf156, arg5_1, arg0_1, arg3_1, buf0, buf159, 32768, 384, grid=grid(32768), stream=stream0)
        del arg3_1
        del arg4_1
        del arg5_1
        del buf0
        buf160 = buf148; del buf148  # reuse
        # Topologically Sorted Source Nodes: [linear_32], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_1.run(arg41_1, buf160, 147456, grid=grid(147456), stream=stream0)
        del arg41_1
        buf161 = buf156; del buf156  # reuse
        # Topologically Sorted Source Nodes: [linear_32], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf159, (32768, 384), (384, 1), 0), reinterpret_tensor(buf160, (384, 384), (1, 384), 0), out=buf161)
        buf164 = buf160; del buf160  # reuse
        # Topologically Sorted Source Nodes: [linear_33], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_1.run(arg42_1, buf164, 147456, grid=grid(147456), stream=stream0)
        del arg42_1
        buf165 = buf149; del buf149  # reuse
        # Topologically Sorted Source Nodes: [linear_33], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf159, (32768, 384), (384, 1), 0), reinterpret_tensor(buf164, (384, 384), (1, 384), 0), out=buf165)
        buf172 = reinterpret_tensor(buf139, (16, 3, 2048, 128), (786432, 128, 384, 1), 0); del buf139  # reuse
        buf173 = reinterpret_tensor(buf129, (16, 3, 2048, 128), (786432, 128, 384, 1), 0); del buf129  # reuse
        # Topologically Sorted Source Nodes: [q_21, q_22, k_26, k_27, y_15], Original ATen: [aten.cat, aten._to_copy, aten.pow, aten.mean, aten._scaled_dot_product_flash_attention]
        stream0 = get_raw_stream(0)
        triton_per_fused__scaled_dot_product_flash_attention__to_copy_cat_mean_pow_2.run(buf161, arg1_1, arg2_1, buf165, buf172, buf173, 98304, 128, grid=grid(98304), stream=stream0)
        del arg1_1
        del arg2_1
        del buf161
        buf168 = buf164; del buf164  # reuse
        # Topologically Sorted Source Nodes: [linear_34], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_1.run(arg43_1, buf168, 147456, grid=grid(147456), stream=stream0)
        del arg43_1
        buf169 = buf165; del buf165  # reuse
        # Topologically Sorted Source Nodes: [linear_34], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf159, (32768, 384), (384, 1), 0), reinterpret_tensor(buf168, (384, 384), (1, 384), 0), out=buf169)
        buf170 = buf107; del buf107  # reuse
        # Topologically Sorted Source Nodes: [linear_35], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_7.run(arg44_1, buf170, 96, grid=grid(96), stream=stream0)
        del arg44_1
        buf171 = buf108; del buf108  # reuse
        # Topologically Sorted Source Nodes: [linear_35], Original ATen: [aten.bmm]
        extern_kernels.bmm(reinterpret_tensor(buf159, (16, 2048, 32), (786432, 384, 1), 0), reinterpret_tensor(buf170, (16, 32, 3), (0, 1, 32), 0), out=buf171)
        del buf159
        del buf170
        buf174 = reinterpret_tensor(buf169, (16, 3, 2048, 128), (786432, 128, 384, 1), 0); del buf169  # reuse
        # Topologically Sorted Source Nodes: [y_15], Original ATen: [aten._scaled_dot_product_flash_attention]
        stream0 = get_raw_stream(0)
        triton_poi_fused__scaled_dot_product_flash_attention_8.run(buf174, buf171, arg0_1, arg40_1, 12582912, grid=grid(12582912), stream=stream0)
        del arg0_1
        del arg40_1
        del buf171
        # Topologically Sorted Source Nodes: [y_15], Original ATen: [aten._scaled_dot_product_flash_attention]
        buf175 = torch.ops.aten._scaled_dot_product_flash_attention.default(buf172, buf173, buf174, 0.0, True, scale=0.08838834764831843)
        del buf172
        del buf173
        buf176 = buf175[0]
        del buf175
        buf181 = buf168; del buf168  # reuse
        # Topologically Sorted Source Nodes: [y_17], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_1.run(arg45_1, buf181, 147456, grid=grid(147456), stream=stream0)
        del arg45_1
        buf182 = reinterpret_tensor(buf174, (32768, 384), (384, 1), 0); del buf174  # reuse
        # Topologically Sorted Source Nodes: [y_17], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf176, (32768, 384), (384, 1), 0), reinterpret_tensor(buf181, (384, 384), (1, 384), 0), out=buf182)
        del buf181
        buf184 = reinterpret_tensor(buf176, (16, 2048, 384), (786432, 384, 1), 0); del buf176  # reuse
        # Topologically Sorted Source Nodes: [x_33, rms_norm_24], Original ATen: [aten.add, aten._to_copy, aten.pow, aten.mean, aten.rsqrt, aten.mul]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_3.run(buf157, buf182, buf184, 32768, 384, grid=grid(32768), stream=stream0)
        buf185 = reinterpret_tensor(buf155, (1536, 384), (384, 1), 0); del buf155  # reuse
        # Topologically Sorted Source Nodes: [x_34], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_4.run(arg46_1, buf185, 589824, grid=grid(589824), stream=stream0)
        del arg46_1
        buf186 = reinterpret_tensor(buf154, (32768, 1536), (1536, 1), 0); del buf154  # reuse
        # Topologically Sorted Source Nodes: [x_34], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf184, (32768, 384), (384, 1), 0), reinterpret_tensor(buf185, (384, 1536), (1, 384), 0), out=buf186)
        buf187 = reinterpret_tensor(buf186, (16, 2048, 1536), (3145728, 1536, 1), 0); del buf186  # reuse
        # Topologically Sorted Source Nodes: [relu_5, x_35, x_36], Original ATen: [aten.relu, aten._to_copy, aten.pow]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_pow_relu_5.run(buf187, 50331648, grid=grid(50331648), stream=stream0)
        buf188 = reinterpret_tensor(buf185, (384, 1536), (1536, 1), 0); del buf185  # reuse
        # Topologically Sorted Source Nodes: [x_36], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_4.run(arg47_1, buf188, 589824, grid=grid(589824), stream=stream0)
        del arg47_1
        buf189 = reinterpret_tensor(buf184, (32768, 384), (384, 1), 0); del buf184  # reuse
        # Topologically Sorted Source Nodes: [x_36], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf187, (32768, 1536), (1536, 1), 0), reinterpret_tensor(buf188, (1536, 384), (1, 1536), 0), out=buf189)
        del buf187
        del buf188
        buf191 = buf157; del buf157  # reuse
        # Topologically Sorted Source Nodes: [x_33, x_37, x_38], Original ATen: [aten.add, aten._to_copy, aten.pow, aten.mean, aten.rsqrt, aten.mul]
        stream0 = get_raw_stream(0)
        triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_13.run(buf191, buf182, buf189, 32768, 384, grid=grid(32768), stream=stream0)
        del buf182
        del buf189
        buf192 = empty_strided_cuda((8192, 384), (384, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [logits], Original ATen: [aten._to_copy]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_14.run(arg48_1, buf192, 3145728, grid=grid(3145728), stream=stream0)
        del arg48_1
        buf193 = empty_strided_cuda((32768, 8192), (8192, 1), torch.bfloat16)
        # Topologically Sorted Source Nodes: [logits], Original ATen: [aten.mm]
        extern_kernels.mm(reinterpret_tensor(buf191, (32768, 384), (384, 1), 0), reinterpret_tensor(buf192, (384, 8192), (1, 384), 0), out=buf193)
        del buf191
        del buf192
        buf194 = empty_strided_cuda((16, 2048, 8192), (16777216, 8192, 1), torch.float32)
        # Topologically Sorted Source Nodes: [logits_1, truediv, tanh, logits_2], Original ATen: [aten._to_copy, aten.div, aten.tanh, aten.mul]
        stream0 = get_raw_stream(0)
        triton_poi_fused__to_copy_div_mul_tanh_15.run(buf193, buf194, 268435456, grid=grid(268435456), stream=stream0)
        del buf193
    return (buf194, )


def benchmark_compiled_module(times=10, repeat=10):
    from torch._dynamo.testing import rand_strided
    from torch._inductor.utils import print_performance
    arg0_1 = rand_strided((16, 2048), (2048, 1), device='cuda:0', dtype=torch.int64)
    arg1_1 = rand_strided((1, 20480, 1, 64), (1310720, 64, 64, 1), device='cuda:0', dtype=torch.bfloat16)
    arg2_1 = rand_strided((1, 20480, 1, 64), (1310720, 64, 64, 1), device='cuda:0', dtype=torch.bfloat16)
    arg3_1 = rand_strided((8192, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    arg4_1 = rand_strided((6, ), (1, ), device='cuda:0', dtype=torch.float32)
    arg5_1 = rand_strided((6, ), (1, ), device='cuda:0', dtype=torch.float32)
    arg6_1 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.float32)
    arg7_1 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.float32)
    arg8_1 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.float32)
    arg9_1 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.float32)
    arg10_1 = rand_strided((1536, 384), (384, 1), device='cuda:0', dtype=torch.float32)
    arg11_1 = rand_strided((384, 1536), (1536, 1), device='cuda:0', dtype=torch.float32)
    arg12_1 = rand_strided((8192, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    arg13_1 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.float32)
    arg14_1 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.float32)
    arg15_1 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.float32)
    arg16_1 = rand_strided((3, 32), (32, 1), device='cuda:0', dtype=torch.float32)
    arg17_1 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.float32)
    arg18_1 = rand_strided((1536, 384), (384, 1), device='cuda:0', dtype=torch.float32)
    arg19_1 = rand_strided((384, 1536), (1536, 1), device='cuda:0', dtype=torch.float32)
    arg20_1 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.float32)
    arg21_1 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.float32)
    arg22_1 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.float32)
    arg23_1 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.float32)
    arg24_1 = rand_strided((1536, 384), (384, 1), device='cuda:0', dtype=torch.float32)
    arg25_1 = rand_strided((384, 1536), (1536, 1), device='cuda:0', dtype=torch.float32)
    arg26_1 = rand_strided((8192, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    arg27_1 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.float32)
    arg28_1 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.float32)
    arg29_1 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.float32)
    arg30_1 = rand_strided((3, 32), (32, 1), device='cuda:0', dtype=torch.float32)
    arg31_1 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.float32)
    arg32_1 = rand_strided((1536, 384), (384, 1), device='cuda:0', dtype=torch.float32)
    arg33_1 = rand_strided((384, 1536), (1536, 1), device='cuda:0', dtype=torch.float32)
    arg34_1 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.float32)
    arg35_1 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.float32)
    arg36_1 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.float32)
    arg37_1 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.float32)
    arg38_1 = rand_strided((1536, 384), (384, 1), device='cuda:0', dtype=torch.float32)
    arg39_1 = rand_strided((384, 1536), (1536, 1), device='cuda:0', dtype=torch.float32)
    arg40_1 = rand_strided((8192, 384), (384, 1), device='cuda:0', dtype=torch.bfloat16)
    arg41_1 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.float32)
    arg42_1 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.float32)
    arg43_1 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.float32)
    arg44_1 = rand_strided((3, 32), (32, 1), device='cuda:0', dtype=torch.float32)
    arg45_1 = rand_strided((384, 384), (384, 1), device='cuda:0', dtype=torch.float32)
    arg46_1 = rand_strided((1536, 384), (384, 1), device='cuda:0', dtype=torch.float32)
    arg47_1 = rand_strided((384, 1536), (1536, 1), device='cuda:0', dtype=torch.float32)
    arg48_1 = rand_strided((8192, 384), (384, 1), device='cuda:0', dtype=torch.float32)
    fn = lambda: call([arg0_1, arg1_1, arg2_1, arg3_1, arg4_1, arg5_1, arg6_1, arg7_1, arg8_1, arg9_1, arg10_1, arg11_1, arg12_1, arg13_1, arg14_1, arg15_1, arg16_1, arg17_1, arg18_1, arg19_1, arg20_1, arg21_1, arg22_1, arg23_1, arg24_1, arg25_1, arg26_1, arg27_1, arg28_1, arg29_1, arg30_1, arg31_1, arg32_1, arg33_1, arg34_1, arg35_1, arg36_1, arg37_1, arg38_1, arg39_1, arg40_1, arg41_1, arg42_1, arg43_1, arg44_1, arg45_1, arg46_1, arg47_1, arg48_1])
    return print_performance(fn, times=times, repeat=repeat)


if __name__ == "__main__":
    from torch._inductor.wrapper_benchmark import compiled_module_main
    compiled_module_main('None', benchmark_compiled_module)
