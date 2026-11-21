
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
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'in_ptr1': '*fp32', 'in_ptr2': '*fp32', 'in_ptr3': '*fp32', 'in_ptr4': '*fp32', 'in_ptr5': '*fp32', 'in_ptr6': '*fp32', 'out_ptr1': '*fp32', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=142, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused__to_copy_add_clamp_min_div_ge_mul_rsqrt_sqrt_sub_11', 'mutated_arg_names': ['in_out_ptr0', 'in_ptr4', 'out_ptr1'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 8, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused__to_copy_add_clamp_min_div_ge_mul_rsqrt_sqrt_sub_11(in_out_ptr0, in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, in_ptr5, in_ptr6, out_ptr1, xnumel, XBLOCK : tl.constexpr):
    xnumel = 128
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = xindex < xnumel
    x3 = xindex
    x0 = (xindex % 32)
    x2 = xindex // 64
    tmp0 = tl.load(in_out_ptr0 + (x3), xmask).to(tl.float32)
    tmp3 = tl.load(in_ptr0 + (x3), xmask).to(tl.float32)
    tmp5 = tl.load(in_ptr1 + (x0 + 32*x2), xmask, eviction_policy='evict_last')
    tmp9 = tl.load(in_ptr2 + (x2), xmask, eviction_policy='evict_last')
    tmp13 = tl.load(in_ptr3 + (x2), xmask, eviction_policy='evict_last')
    tmp20 = tl.load(in_ptr4 + (x3), xmask)
    tmp21 = tl.load(in_ptr5 + (0))
    tmp22 = tl.broadcast_to(tmp21, [XBLOCK])
    tmp26 = tl.load(in_ptr6 + (0))
    tmp27 = tl.broadcast_to(tmp26, [XBLOCK])
    tmp1 = 2.3465413258596377
    tmp2 = tmp0 * tmp1
    tmp4 = tmp2 + tmp3
    tmp6 = 1e-10
    tmp7 = triton_helpers.maximum(tmp5, tmp6)
    tmp8 = libdevice.rsqrt(tmp7)
    tmp10 = 2.0
    tmp11 = tmp9 * tmp10
    tmp12 = libdevice.sqrt(tmp11)
    tmp14 = libdevice.sqrt(tmp13)
    tmp15 = triton_helpers.maximum(tmp14, tmp6)
    tmp16 = tmp12 / tmp15
    tmp17 = tmp8 * tmp16
    tmp18 = tmp17.to(tl.float32)
    tmp19 = tmp4 * tmp18
    tmp23 = tmp22.to(tl.float32)
    tmp24 = tmp23 * tmp19
    tmp25 = tmp24.to(tl.float32)
    tmp28 = tmp27.to(tl.float32)
    tmp29 = tmp23 * tmp28
    tmp30 = tmp29.to(tl.float32)
    tmp31 = tmp30 * tmp20
    tmp32 = tmp19.to(tl.float32)
    tmp33 = tmp32 * tmp20
    tmp34 = 0.0
    tmp35 = tmp33 >= tmp34
    tmp36 = tmp35.to(tl.float32)
    tmp37 = tmp31 * tmp36
    tmp38 = tmp25 + tmp37
    tmp39 = tmp20 - tmp38
    tl.store(out_ptr1 + (x3), tmp39, xmask)
