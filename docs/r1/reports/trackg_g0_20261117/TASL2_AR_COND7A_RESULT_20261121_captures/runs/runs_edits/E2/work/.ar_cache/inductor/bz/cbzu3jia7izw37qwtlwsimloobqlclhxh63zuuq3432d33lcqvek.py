
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
    triton_meta={'signature': {'in_ptr0': '*fp32', 'in_ptr1': '*fp32', 'in_ptr2': '*bf16', 'in_ptr3': '*bf16', 'in_ptr4': '*bf16', 'in_ptr5': '*fp32', 'out_ptr1': '*fp32', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused__to_copy_add_clamp_min_div_ge_lerp_mean_mul_pow_rsqrt_rsub_sqrt_sub_14', 'mutated_arg_names': ['in_ptr0', 'out_ptr1'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 6, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused__to_copy_add_clamp_min_div_ge_lerp_mean_mul_pow_rsqrt_rsub_sqrt_sub_14(in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, in_ptr5, out_ptr1, xnumel, XBLOCK : tl.constexpr):
    xnumel = 3538944
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x2 = xindex
    x1 = xindex // 384
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
