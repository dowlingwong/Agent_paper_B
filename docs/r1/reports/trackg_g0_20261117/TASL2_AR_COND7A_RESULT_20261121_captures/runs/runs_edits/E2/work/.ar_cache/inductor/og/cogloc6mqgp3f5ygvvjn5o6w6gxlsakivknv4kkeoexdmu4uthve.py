
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
