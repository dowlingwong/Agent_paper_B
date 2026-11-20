
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
    triton_meta={'signature': {'in_ptr0': '*fp32', 'in_ptr1': '*fp32', 'in_ptr2': '*fp32', 'in_ptr3': '*fp32', 'in_ptr4': '*fp32', 'in_ptr5': '*fp32', 'in_ptr6': '*fp32', 'in_ptr7': '*fp32', 'in_ptr8': '*fp32', 'in_ptr9': '*fp32', 'out_ptr4': '*fp32', 'out_ptr5': '*fp32', 'out_ptr6': '*fp32', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=142, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_add_div_lerp_mul_neg_pow_rsub_sqrt_0', 'mutated_arg_names': ['in_ptr2', 'in_ptr4', 'in_ptr7', 'out_ptr4', 'out_ptr5', 'out_ptr6'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 10, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_add_div_lerp_mul_neg_pow_rsub_sqrt_0(in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, in_ptr5, in_ptr6, in_ptr7, in_ptr8, in_ptr9, out_ptr4, out_ptr5, out_ptr6, xnumel, XBLOCK : tl.constexpr):
    xnumel = 4
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = xindex < xnumel
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (0))
    tmp1 = tl.broadcast_to(tmp0, [XBLOCK])
    tmp9 = tl.load(in_ptr1 + (x0), xmask)
    tmp10 = tl.load(in_ptr2 + (x0), xmask)
    tmp15 = tl.load(in_ptr3 + (0))
    tmp16 = tl.broadcast_to(tmp15, [XBLOCK])
    tmp23 = tl.load(in_ptr4 + (x0), xmask)
    tmp28 = tl.load(in_ptr5 + (0))
    tmp29 = tl.broadcast_to(tmp28, [XBLOCK])
    tmp34 = tl.load(in_ptr6 + (0))
    tmp35 = tl.broadcast_to(tmp34, [XBLOCK])
    tmp38 = tl.load(in_ptr7 + (x0), xmask)
    tmp39 = tl.load(in_ptr8 + (0))
    tmp40 = tl.broadcast_to(tmp39, [XBLOCK])
    tmp41 = tl.load(in_ptr9 + (0))
    tmp42 = tl.broadcast_to(tmp41, [XBLOCK])
    tmp2 = 1.0
    tmp3 = tmp2 - tmp1
    tmp4 = tl_math.abs(tmp3)
    tmp5 = 0.5
    tmp6 = tmp4 >= tmp5
    tmp7 = tmp3 - tmp2
    tmp8 = tl.where(tmp6, tmp7, tmp3)
    tmp11 = tmp9 - tmp10
    tmp12 = tmp8 * tmp11
    tmp13 = tl.where(tmp6, tmp9, tmp10)
    tmp14 = tmp12 + tmp13
    tmp17 = tmp2 - tmp16
    tmp18 = tl_math.abs(tmp17)
    tmp19 = tmp18 >= tmp5
    tmp20 = tmp17 - tmp2
    tmp21 = tl.where(tmp19, tmp20, tmp17)
    tmp22 = tmp9 * tmp9
    tmp24 = tmp22 - tmp23
    tmp25 = tmp21 * tmp24
    tmp26 = tl.where(tmp19, tmp22, tmp23)
    tmp27 = tmp25 + tmp26
    tmp30 = libdevice.pow(tmp16, tmp29)
    tmp31 = tmp2 - tmp30
    tmp32 = tmp27 / tmp31
    tmp33 = libdevice.sqrt(tmp32)
    tmp36 = tmp33 + tmp35
    tmp37 = tmp14 / tmp36
    tmp43 = tmp40 * tmp42
    tmp44 = tmp2 - tmp43
    tmp45 = tmp38 * tmp44
    tmp46 = libdevice.pow(tmp1, tmp29)
    tmp47 = tmp2 - tmp46
    tmp48 = tmp40 / tmp47
    tmp49 = -tmp48
    tmp50 = tmp37 * tmp49
    tmp51 = tmp45 + tmp50
    tl.store(out_ptr4 + (x0), tmp14, xmask)
    tl.store(out_ptr5 + (x0), tmp27, xmask)
    tl.store(out_ptr6 + (x0), tmp51, xmask)
