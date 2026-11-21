
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
