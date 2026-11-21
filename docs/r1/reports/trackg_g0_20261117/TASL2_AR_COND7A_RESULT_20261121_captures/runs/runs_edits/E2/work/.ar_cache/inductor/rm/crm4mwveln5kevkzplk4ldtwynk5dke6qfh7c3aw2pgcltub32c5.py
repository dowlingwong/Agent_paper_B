
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.reduction(
    size_hints={'x': 8, 'r': 2048},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*fp32', 'in_ptr1': '*fp32', 'in_ptr2': '*fp32', 'out_ptr2': '*bf16', 'out_ptr4': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 6), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_red_fused__to_copy_add_clamp_min_div_lerp_mean_mul_pow_rsqrt_rsub_sqrt_sum_13', 'mutated_arg_names': ['in_ptr2', 'out_ptr4'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 6, 'num_reduction': 2, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_red_fused__to_copy_add_clamp_min_div_lerp_mean_mul_pow_rsqrt_rsub_sqrt_sum_13(in_ptr0, in_ptr1, in_ptr2, out_ptr2, out_ptr4, xnumel, rnumel, XBLOCK : tl.constexpr, RBLOCK : tl.constexpr):
    xnumel = 6
    rnumel = 1536
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:, None]
    xmask = xindex < xnumel
    rbase = tl.arange(0, RBLOCK)[None, :]
    x0 = xindex
    _tmp4 = tl.full([XBLOCK, RBLOCK], 0, tl.float32)
    tmp7 = tl.load(in_ptr1 + (0))
    tmp8 = tl.broadcast_to(tmp7, [XBLOCK, RBLOCK])
    _tmp27 = tl.full([XBLOCK, RBLOCK], 0, tl.float32)
    for roffset in range(0, rnumel, RBLOCK):
        rindex = roffset + rbase
        rmask = rindex < rnumel
        r1 = rindex
        tmp0 = tl.load(in_ptr0 + (r1 + 1536*x0), rmask & xmask, eviction_policy='evict_last', other=0.0)
        tmp16 = tl.load(in_ptr2 + (r1 + 1536*x0), rmask & xmask, eviction_policy='evict_last', other=0.0)
        tmp1 = 384.0
        tmp2 = tmp0 / tmp1
        tmp3 = tl.broadcast_to(tmp2, [XBLOCK, RBLOCK])
        tmp5 = _tmp4 + tmp3
        _tmp4 = tl.where(rmask & xmask, tmp5, _tmp4)
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
        tmp26 = tl.broadcast_to(tmp25, [XBLOCK, RBLOCK])
        tmp28 = _tmp27 + tmp26
        _tmp27 = tl.where(rmask & xmask, tmp28, _tmp27)
    tmp4 = tl.sum(_tmp4, 1)[:, None]
    tmp27 = tl.sum(_tmp27, 1)[:, None]
    tmp29 = tl.load(in_ptr1 + (0))
    tmp30 = tl.broadcast_to(tmp29, [XBLOCK, RBLOCK])
    for roffset in range(0, rnumel, RBLOCK):
        rindex = roffset + rbase
        rmask = rindex < rnumel
        r1 = rindex
        tmp38 = tl.load(in_ptr0 + (r1 + 1536*x0), rmask & xmask, eviction_policy='evict_first', other=0.0)
        tmp41 = tl.load(in_ptr2 + (r1 + 1536*x0), rmask & xmask, eviction_policy='evict_first', other=0.0)
        tmp31 = 1.0
        tmp32 = tmp31 - tmp30
        tmp33 = tl_math.abs(tmp32)
        tmp34 = 0.5
        tmp35 = tmp33 >= tmp34
        tmp36 = tmp32 - tmp31
        tmp37 = tl.where(tmp35, tmp36, tmp32)
        tmp39 = 384.0
        tmp40 = tmp38 / tmp39
        tmp42 = tmp40 - tmp41
        tmp43 = tmp37 * tmp42
        tmp44 = tl.where(tmp35, tmp40, tmp41)
        tmp45 = tmp43 + tmp44
        tmp46 = 1e-10
        tmp47 = triton_helpers.maximum(tmp45, tmp46)
        tmp48 = libdevice.rsqrt(tmp47)
        tmp49 = tmp4 * tmp39
        tmp50 = libdevice.sqrt(tmp49)
        tmp51 = libdevice.sqrt(tmp27)
        tmp52 = triton_helpers.maximum(tmp51, tmp46)
        tmp53 = tmp50 / tmp52
        tmp54 = tmp48 * tmp53
        tmp55 = tmp54.to(tl.float32)
        tl.store(out_ptr2 + (r1 + 1536*x0), tmp55, rmask & xmask)
        tl.store(out_ptr4 + (r1 + 1536*x0), tmp45, rmask & xmask)
