
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
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'in_ptr3': '*bf16', 'in_ptr4': '*fp32', 'in_ptr5': '*bf16', 'in_ptr6': '*fp32', 'out_ptr1': '*bf16', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_red_fused__to_copy_add_div_mul_pow_slice_backward_sum_12', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 13, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_red_fused__to_copy_add_div_mul_pow_slice_backward_sum_12(in_out_ptr0, in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, in_ptr5, in_ptr6, out_ptr1, xnumel, rnumel, XBLOCK : tl.constexpr, RBLOCK : tl.constexpr):
    xnumel = 32768
    rnumel = 384
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:, None]
    xmask = tl.full([XBLOCK, RBLOCK], True, tl.int1)
    rbase = tl.arange(0, RBLOCK)[None, :]
    x0 = xindex
    _tmp17 = tl.full([XBLOCK, RBLOCK], 0, tl.float32)
    for roffset in range(0, rnumel, RBLOCK):
        rindex = roffset + rbase
        rmask = rindex < rnumel
        r1 = rindex
        tmp6 = tl.load(in_out_ptr0 + (r1 + 384*x0), rmask, eviction_policy='evict_last', other=0.0).to(tl.float32)
        tmp8 = tl.load(in_ptr1 + (r1 + 384*x0), rmask, eviction_policy='evict_last', other=0.0).to(tl.float32)
        tmp10 = tl.load(in_ptr2 + (r1 + 384*x0), rmask, eviction_policy='evict_last', other=0.0).to(tl.float32)
        tmp13 = tl.load(in_ptr3 + (r1 + 384*x0), rmask, eviction_policy='evict_last', other=0.0).to(tl.float32)
        tmp0 = r1
        tmp1 = tl.full([1, 1], 32, tl.int64)
        tmp2 = tmp0 < tmp1
        tmp3 = tl.load(in_ptr0 + (r1 + 32*x0), rmask & tmp2, eviction_policy='evict_last', other=0.0).to(tl.float32)
        tmp4 = 0.0
        tmp5 = tl.where(tmp2, tmp3, tmp4)
        tmp7 = tmp5 + tmp6
        tmp9 = tmp7 + tmp8
        tmp11 = tmp9 + tmp10
        tmp12 = tmp11.to(tl.float32)
        tmp14 = tmp13.to(tl.float32)
        tmp15 = tmp12 * tmp14
        tmp16 = tl.broadcast_to(tmp15, [XBLOCK, RBLOCK])
        tmp18 = _tmp17 + tmp16
        _tmp17 = tl.where(rmask, tmp18, _tmp17)
    tmp17 = tl.sum(_tmp17, 1)[:, None]
    tmp32 = tl.load(in_ptr4 + (x0), None, eviction_policy='evict_last')
    tmp50 = tl.load(in_ptr6 + (5))
    tmp51 = tl.broadcast_to(tmp50, [XBLOCK, RBLOCK])
    for roffset in range(0, rnumel, RBLOCK):
        rindex = roffset + rbase
        rmask = rindex < rnumel
        r1 = rindex
        tmp25 = tl.load(in_out_ptr0 + (r1 + 384*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp27 = tl.load(in_ptr1 + (r1 + 384*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp29 = tl.load(in_ptr2 + (r1 + 384*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp41 = tl.load(in_ptr3 + (r1 + 384*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp48 = tl.load(in_ptr5 + (r1 + 384*x0), rmask, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp19 = r1
        tmp20 = tl.full([1, 1], 32, tl.int64)
        tmp21 = tmp19 < tmp20
        tmp22 = tl.load(in_ptr0 + (r1 + 32*x0), rmask & tmp21, eviction_policy='evict_first', other=0.0).to(tl.float32)
        tmp23 = 0.0
        tmp24 = tl.where(tmp21, tmp22, tmp23)
        tmp26 = tmp24 + tmp25
        tmp28 = tmp26 + tmp27
        tmp30 = tmp28 + tmp29
        tmp31 = tmp30.to(tl.float32)
        tmp33 = tmp31 * tmp32
        tmp34 = -0.5
        tmp35 = tmp17 * tmp34
        tmp36 = tmp32 * tmp32
        tmp37 = tmp36 * tmp32
        tmp38 = tmp35 * tmp37
        tmp39 = 0.0026041666666666665
        tmp40 = tmp38 * tmp39
        tmp42 = tmp41.to(tl.float32)
        tmp43 = 2.0
        tmp44 = tmp42 * tmp43
        tmp45 = tmp40 * tmp44
        tmp46 = tmp33 + tmp45
        tmp47 = tmp46.to(tl.float32)
        tmp49 = tmp48 + tmp47
        tmp52 = tmp51.to(tl.float32)
        tmp53 = tmp49 * tmp52
        tl.store(in_out_ptr0 + (r1 + 384*x0), tmp47, rmask)
        tl.store(out_ptr1 + (r1 + 384*x0), tmp53, rmask)
