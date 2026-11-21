
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
