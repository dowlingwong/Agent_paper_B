
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 32768, 'r': 512},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_out_ptr1': '*bf16', 'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'in_ptr3': '*bf16', 'in_ptr4': '*fp32', 'in_ptr5': '*bf16', 'in_ptr6': '*fp32', 'in_ptr7': '*bf16', 'in_ptr8': '*bf16', 'in_ptr9': '*bf16', 'in_ptr10': '*fp32', 'in_ptr11': '*bf16', 'in_ptr12': '*fp32', 'in_ptr13': '*bf16', 'in_ptr14': '*bf16', 'out_ptr1': '*bf16', 'out_ptr2': '*fp32', 'out_ptr3': '*fp32', 'out_ptr4': '*fp32', 'out_ptr5': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_div_mul_pow_sum_view_20', 'mutated_arg_names': ['in_out_ptr0', 'in_out_ptr1'], 'optimize_mem': True, 'no_x_dim': True, 'num_load': 20, 'num_reduction': 5, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_div_mul_pow_sum_view_20(in_out_ptr0, in_out_ptr1, in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, in_ptr5, in_ptr6, in_ptr7, in_ptr8, in_ptr9, in_ptr10, in_ptr11, in_ptr12, in_ptr13, in_ptr14, out_ptr1, out_ptr2, out_ptr3, out_ptr4, out_ptr5, xnumel, rnumel):
    xnumel = 32768
    XBLOCK: tl.constexpr = 1
    rnumel = 384
    RBLOCK: tl.constexpr = 512
    xoffset = tl.program_id(0) * XBLOCK
    xindex = tl.full([1], xoffset, tl.int32)
    xmask = tl.full([RBLOCK], True, tl.int1)
    rindex = tl.arange(0, RBLOCK)[:]
    roffset = 0
    rmask = rindex < rnumel
    r1 = rindex
    x0 = xindex
    tmp0 = tl.load(in_out_ptr0 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp1 = tl.load(in_ptr0 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp3 = tl.load(in_ptr1 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp6 = tl.load(in_ptr2 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp13 = tl.load(in_ptr3 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp14 = tl.load(in_ptr4 + (x0), None, eviction_policy='evict_last')
    tmp29 = tl.load(in_out_ptr1 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp30 = tl.load(in_ptr5 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp32 = tl.load(in_ptr6 + (5))
    tmp33 = tl.broadcast_to(tmp32, [RBLOCK])
    tmp36 = tl.load(in_ptr7 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp37 = tl.load(in_ptr6 + (4))
    tmp38 = tl.broadcast_to(tmp37, [RBLOCK])
    tmp42 = tl.load(in_ptr8 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp43 = tl.load(in_ptr9 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp45 = tl.load(in_ptr6 + (3))
    tmp46 = tl.broadcast_to(tmp45, [RBLOCK])
    tmp50 = tl.load(in_ptr6 + (2))
    tmp51 = tl.broadcast_to(tmp50, [RBLOCK])
    tmp55 = tl.load(in_ptr10 + (2))
    tmp56 = tl.broadcast_to(tmp55, [RBLOCK])
    tmp59 = tl.load(in_ptr11 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp61 = tl.load(in_ptr12 + (x0), None, eviction_policy='evict_last')
    tmp70 = tl.load(in_ptr13 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp83 = tl.load(in_ptr14 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp2 = tmp0 + tmp1
    tmp4 = tmp2 + tmp3
    tmp5 = tmp4.to(tl.float32)
    tmp7 = tmp6.to(tl.float32)
    tmp8 = tmp5 * tmp7
    tmp9 = tl.broadcast_to(tmp8, [RBLOCK])
    tmp11 = tl.where(rmask, tmp9, 0)
    tmp12 = triton_helpers.promote_to_tensor(tl.sum(tmp11, 0))
    tmp15 = tmp5 * tmp14
    tmp16 = -0.5
    tmp17 = tmp12 * tmp16
    tmp18 = tmp14 * tmp14
    tmp19 = tmp18 * tmp14
    tmp20 = tmp17 * tmp19
    tmp21 = 0.0026041666666666665
    tmp22 = tmp20 * tmp21
    tmp23 = 2.0
    tmp24 = tmp7 * tmp23
    tmp25 = tmp22 * tmp24
    tmp26 = tmp15 + tmp25
    tmp27 = tmp26.to(tl.float32)
    tmp28 = tmp13 + tmp27
    tmp31 = tmp29 + tmp30
    tmp34 = tmp33.to(tl.float32)
    tmp35 = tmp31 * tmp34
    tmp39 = tmp38.to(tl.float32)
    tmp40 = tmp36 * tmp39
    tmp41 = tmp35 + tmp40
    tmp44 = tmp42 + tmp43
    tmp47 = tmp46.to(tl.float32)
    tmp48 = tmp44 * tmp47
    tmp49 = tmp41 + tmp48
    tmp52 = tmp51.to(tl.float32)
    tmp53 = tmp28 * tmp52
    tmp54 = tmp49 + tmp53
    tmp57 = tmp56.to(tl.float32)
    tmp58 = tmp28 * tmp57
    tmp60 = tmp59.to(tl.float32)
    tmp62 = tmp60 * tmp61
    tmp63 = tmp62.to(tl.float32)
    tmp64 = tmp44 * tmp63
    tmp65 = tmp64.to(tl.float32)
    tmp66 = tl.broadcast_to(tmp65, [RBLOCK])
    tmp68 = tl.where(rmask, tmp66, 0)
    tmp69 = triton_helpers.promote_to_tensor(tl.sum(tmp68, 0))
    tmp71 = tmp44 * tmp70
    tmp72 = tmp71.to(tl.float32)
    tmp73 = tl.broadcast_to(tmp72, [RBLOCK])
    tmp75 = tl.where(rmask, tmp73, 0)
    tmp76 = triton_helpers.promote_to_tensor(tl.sum(tmp75, 0))
    tmp77 = tmp28 * tmp63
    tmp78 = tmp77.to(tl.float32)
    tmp79 = tl.broadcast_to(tmp78, [RBLOCK])
    tmp81 = tl.where(rmask, tmp79, 0)
    tmp82 = triton_helpers.promote_to_tensor(tl.sum(tmp81, 0))
    tmp84 = tmp28 * tmp83
    tmp85 = tmp84.to(tl.float32)
    tmp86 = tl.broadcast_to(tmp85, [RBLOCK])
    tmp88 = tl.where(rmask, tmp86, 0)
    tmp89 = triton_helpers.promote_to_tensor(tl.sum(tmp88, 0))
    tl.store(in_out_ptr0 + (r1 + 384*x0), tmp28, rmask)
    tl.store(in_out_ptr1 + (r1 + 384*x0), tmp54, rmask)
    tl.store(out_ptr1 + (r1 + 384*x0), tmp58, rmask)
    tl.store(out_ptr2 + (x0), tmp69, None)
    tl.store(out_ptr3 + (x0), tmp76, None)
    tl.store(out_ptr4 + (x0), tmp82, None)
    tl.store(out_ptr5 + (x0), tmp89, None)
