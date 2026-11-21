
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
    triton_meta={'signature': {'in_ptr0': '*fp32', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'in_ptr3': '*fp32', 'in_ptr4': '*bf16', 'in_ptr5': '*fp32', 'in_ptr6': '*fp32', 'in_ptr7': '*bf16', 'in_ptr8': '*fp32', 'in_ptr9': '*fp32', 'out_ptr4': '*bf16', 'out_ptr5': '*bf16', 'out_ptr6': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=142, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused__to_copy_add_div_lerp_mul_neg_pow_rsub_sqrt_0', 'mutated_arg_names': ['in_ptr2', 'in_ptr4', 'in_ptr7', 'out_ptr4', 'out_ptr5', 'out_ptr6'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 10, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused__to_copy_add_div_lerp_mul_neg_pow_rsub_sqrt_0(in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, in_ptr5, in_ptr6, in_ptr7, in_ptr8, in_ptr9, out_ptr4, out_ptr5, out_ptr6, xnumel, XBLOCK : tl.constexpr):
    xnumel = 2097152
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (0))
    tmp1 = tl.broadcast_to(tmp0, [XBLOCK])
    tmp11 = tl.load(in_ptr1 + (x0), None).to(tl.float32)
    tmp13 = tl.load(in_ptr2 + (x0), None).to(tl.float32)
    tmp20 = tl.load(in_ptr3 + (0))
    tmp21 = tl.broadcast_to(tmp20, [XBLOCK])
    tmp31 = tl.load(in_ptr4 + (x0), None).to(tl.float32)
    tmp38 = tl.load(in_ptr5 + (0))
    tmp39 = tl.broadcast_to(tmp38, [XBLOCK])
    tmp45 = tl.load(in_ptr6 + (0))
    tmp46 = tl.broadcast_to(tmp45, [XBLOCK])
    tmp50 = tl.load(in_ptr7 + (x0), None).to(tl.float32)
    tmp51 = tl.load(in_ptr8 + (0))
    tmp52 = tl.broadcast_to(tmp51, [XBLOCK])
    tmp54 = tl.load(in_ptr9 + (0))
    tmp55 = tl.broadcast_to(tmp54, [XBLOCK])
    tmp2 = tmp1.to(tl.float32)
    tmp3 = 1.0
    tmp4 = tmp3 - tmp2
    tmp5 = tmp4.to(tl.float32)
    tmp6 = tl_math.abs(tmp5)
    tmp7 = 0.5
    tmp8 = tmp6 >= tmp7
    tmp9 = tmp5 - tmp3
    tmp10 = tl.where(tmp8, tmp9, tmp5)
    tmp12 = tmp11.to(tl.float32)
    tmp14 = tmp13.to(tl.float32)
    tmp15 = tmp12 - tmp14
    tmp16 = tmp10 * tmp15
    tmp17 = tl.where(tmp8, tmp12, tmp14)
    tmp18 = tmp16 + tmp17
    tmp19 = tmp18.to(tl.float32)
    tmp22 = tmp21.to(tl.float32)
    tmp23 = tmp3 - tmp22
    tmp24 = tmp23.to(tl.float32)
    tmp25 = tl_math.abs(tmp24)
    tmp26 = tmp25 >= tmp7
    tmp27 = tmp24 - tmp3
    tmp28 = tl.where(tmp26, tmp27, tmp24)
    tmp29 = tmp11 * tmp11
    tmp30 = tmp29.to(tl.float32)
    tmp32 = tmp31.to(tl.float32)
    tmp33 = tmp30 - tmp32
    tmp34 = tmp28 * tmp33
    tmp35 = tl.where(tmp26, tmp30, tmp32)
    tmp36 = tmp34 + tmp35
    tmp37 = tmp36.to(tl.float32)
    tmp40 = tmp39.to(tl.float32)
    tmp41 = libdevice.pow(tmp22, tmp40)
    tmp42 = tmp3 - tmp41
    tmp43 = tmp37 / tmp42
    tmp44 = libdevice.sqrt(tmp43)
    tmp47 = tmp46.to(tl.float32)
    tmp48 = tmp44 + tmp47
    tmp49 = tmp19 / tmp48
    tmp53 = tmp52.to(tl.float32)
    tmp56 = tmp55.to(tl.float32)
    tmp57 = tmp53 * tmp56
    tmp58 = tmp3 - tmp57
    tmp59 = tmp50 * tmp58
    tmp60 = libdevice.pow(tmp2, tmp40)
    tmp61 = tmp3 - tmp60
    tmp62 = tmp53 / tmp61
    tmp63 = -tmp62
    tmp64 = tmp49 * tmp63
    tmp65 = tmp59 + tmp64
    tl.store(out_ptr4 + (x0), tmp19, None)
    tl.store(out_ptr5 + (x0), tmp37, None)
    tl.store(out_ptr6 + (x0), tmp65, None)
