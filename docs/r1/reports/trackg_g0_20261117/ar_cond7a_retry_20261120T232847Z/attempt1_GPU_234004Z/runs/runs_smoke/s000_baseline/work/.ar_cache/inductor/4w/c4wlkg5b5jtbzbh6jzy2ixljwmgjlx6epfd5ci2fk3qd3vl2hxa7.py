
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 2, 'r': 32},
    reduction_hint=ReductionHint.DEFAULT,
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*fp32', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'in_ptr3': '*fp32', 'out_ptr0': '*fp32', 'out_ptr1': '*fp32', 'out_ptr2': '*fp32', 'out_ptr3': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=142, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 9), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_clamp_min_lerp_mean_mul_pow_rsqrt_rsub_sum_10', 'mutated_arg_names': ['in_ptr3', 'out_ptr1'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 6, 'num_reduction': 2, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_clamp_min_lerp_mean_mul_pow_rsqrt_rsub_sum_10(in_ptr0, in_ptr1, in_ptr2, in_ptr3, out_ptr0, out_ptr1, out_ptr2, out_ptr3, xnumel, rnumel, XBLOCK : tl.constexpr):
    xnumel = 2
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
    tmp0 = tl.load(in_ptr0 + (0))
    tmp1 = tl.broadcast_to(tmp0, [XBLOCK, RBLOCK])
    tmp9 = tl.load(in_ptr1 + (r1 + 64*x0), xmask, other=0.0).to(tl.float32)
    tmp12 = tl.load(in_ptr2 + (r1 + 64*x0), xmask, other=0.0).to(tl.float32)
    tmp16 = tl.load(in_ptr1 + (32 + r1 + 64*x0), xmask, other=0.0).to(tl.float32)
    tmp18 = tl.load(in_ptr2 + (32 + r1 + 64*x0), xmask, other=0.0).to(tl.float32)
    tmp25 = tl.load(in_ptr3 + (r1 + 32*x0), xmask, other=0.0)
    tmp2 = 1.0
    tmp3 = tmp2 - tmp1
    tmp4 = tl_math.abs(tmp3)
    tmp5 = 0.5
    tmp6 = tmp4 >= tmp5
    tmp7 = tmp3 - tmp2
    tmp8 = tl.where(tmp6, tmp7, tmp3)
    tmp10 = 2.3465413258596377
    tmp11 = tmp9 * tmp10
    tmp13 = tmp11 + tmp12
    tmp14 = tmp13.to(tl.float32)
    tmp15 = tmp14 * tmp14
    tmp17 = tmp16 * tmp10
    tmp19 = tmp17 + tmp18
    tmp20 = tmp19.to(tl.float32)
    tmp21 = tmp20 * tmp20
    tmp22 = tmp15 + tmp21
    tmp23 = 2.0
    tmp24 = tmp22 / tmp23
    tmp26 = tmp24 - tmp25
    tmp27 = tmp8 * tmp26
    tmp28 = tl.where(tmp6, tmp24, tmp25)
    tmp29 = tmp27 + tmp28
    tmp30 = tl.broadcast_to(tmp24, [XBLOCK, RBLOCK])
    tmp32 = tl.where(xmask, tmp30, 0)
    tmp33 = tl.sum(tmp32, 1)[:, None]
    tmp34 = tmp24 * tmp23
    tmp35 = 1e-10
    tmp36 = triton_helpers.maximum(tmp29, tmp35)
    tmp37 = libdevice.rsqrt(tmp36)
    tmp38 = tmp37 * tmp37
    tmp39 = tmp34 * tmp38
    tmp40 = tl.broadcast_to(tmp39, [XBLOCK, RBLOCK])
    tmp42 = tl.where(xmask, tmp40, 0)
    tmp43 = tl.sum(tmp42, 1)[:, None]
    tl.store(out_ptr0 + (r1 + 32*x0), tmp29, xmask)
    tl.store(out_ptr1 + (r1 + 32*x0), tmp29, xmask)
    tl.store(out_ptr2 + (x0), tmp33, xmask)
    tl.store(out_ptr3 + (x0), tmp43, xmask)
