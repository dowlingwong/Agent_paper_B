
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 32768, 'r': 256},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'in_ptr3': '*fp32', 'in_ptr4': '*bf16', 'in_ptr5': '*bf16', 'in_ptr6': '*bf16', 'in_ptr7': '*bf16', 'in_ptr8': '*fp32', 'in_ptr9': '*fp32', 'in_ptr10': '*fp32', 'in_ptr11': '*bf16', 'in_ptr12': '*bf16', 'in_ptr13': '*bf16', 'in_ptr14': '*i64', 'in_ptr15': '*bf16', 'in_ptr16': '*bf16', 'out_ptr0': '*fp32', 'out_ptr1': '*fp32', 'out_ptr4': '*fp32', 'out_ptr6': '*fp32', 'out_ptr7': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=142, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_div_embedding_dense_backward_mul_nll_loss_forward_pow_sum_21', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': True, 'num_load': 21, 'num_reduction': 5, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_div_embedding_dense_backward_mul_nll_loss_forward_pow_sum_21(in_out_ptr0, in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, in_ptr5, in_ptr6, in_ptr7, in_ptr8, in_ptr9, in_ptr10, in_ptr11, in_ptr12, in_ptr13, in_ptr14, in_ptr15, in_ptr16, out_ptr0, out_ptr1, out_ptr4, out_ptr6, out_ptr7, xnumel, rnumel):
    xnumel = 32768
    XBLOCK: tl.constexpr = 1
    rnumel = 256
    RBLOCK: tl.constexpr = 256
    xoffset = tl.program_id(0) * XBLOCK
    xindex = tl.full([1], xoffset, tl.int32)
    xmask = tl.full([RBLOCK], True, tl.int1)
    rindex = tl.arange(0, RBLOCK)[:]
    roffset = 0
    rmask = tl.full([RBLOCK], True, tl.int1)
    r1 = rindex
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (r1 + 256*x0), None).to(tl.float32)
    tmp1 = tl.load(in_ptr1 + (r1 + 256*x0), None).to(tl.float32)
    tmp3 = tl.load(in_ptr2 + (r1 + 256*x0), None).to(tl.float32)
    tmp5 = tl.load(in_ptr3 + (x0), None, eviction_policy='evict_last')
    tmp13 = tl.load(in_ptr4 + (r1 + 256*x0), None).to(tl.float32)
    tmp19 = tl.load(in_ptr5 + (r1 + 256*x0), None).to(tl.float32)
    tmp20 = tl.load(in_ptr6 + (r1 + 256*x0), None).to(tl.float32)
    tmp22 = tl.load(in_ptr7 + (r1 + 256*x0), None).to(tl.float32)
    tmp25 = tl.load(in_ptr8 + (0))
    tmp26 = tl.broadcast_to(tmp25, [RBLOCK])
    tmp29 = tl.load(in_ptr9 + (0))
    tmp30 = tl.broadcast_to(tmp29, [RBLOCK])
    tmp39 = tl.load(in_ptr10 + (x0), None, eviction_policy='evict_last')
    tmp52 = tl.load(in_out_ptr0 + (r1 + 256*x0), None).to(tl.float32)
    tmp53 = tl.load(in_ptr11 + (r1 + 256*x0), None).to(tl.float32)
    tmp55 = tl.load(in_ptr9 + (3))
    tmp56 = tl.broadcast_to(tmp55, [RBLOCK])
    tmp59 = tl.load(in_ptr12 + (r1 + 256*x0), None).to(tl.float32)
    tmp60 = tl.load(in_ptr9 + (2))
    tmp61 = tl.broadcast_to(tmp60, [RBLOCK])
    tmp65 = tl.load(in_ptr9 + (1))
    tmp66 = tl.broadcast_to(tmp65, [RBLOCK])
    tmp70 = tl.load(in_ptr13 + (r1 + 256*x0), None).to(tl.float32)
    tmp87 = tl.load(in_ptr14 + (x0), None, eviction_policy='evict_last')
    tmp90 = tl.load(in_ptr15 + (r1 + 256*x0), None).to(tl.float32)
    tmp91 = tl.load(in_ptr16 + (2*x0 + (r1 // 128)), None, eviction_policy='evict_last').to(tl.float32)
    tmp2 = tmp0 + tmp1
    tmp4 = tmp3.to(tl.float32)
    tmp6 = tmp4 * tmp5
    tmp7 = tmp6.to(tl.float32)
    tmp8 = tmp2 * tmp7
    tmp9 = tmp8.to(tl.float32)
    tmp10 = tl.broadcast_to(tmp9, [RBLOCK])
    tmp12 = triton_helpers.promote_to_tensor(tl.sum(tmp10, 0))
    tmp14 = tmp2 * tmp13
    tmp15 = tmp14.to(tl.float32)
    tmp16 = tl.broadcast_to(tmp15, [RBLOCK])
    tmp18 = triton_helpers.promote_to_tensor(tl.sum(tmp16, 0))
    tmp21 = tmp19 + tmp20
    tmp23 = tmp21 + tmp22
    tmp24 = tmp23.to(tl.float32)
    tmp27 = tmp26.to(tl.float32)
    tmp28 = tmp27 * tmp7
    tmp31 = tmp30.to(tl.float32)
    tmp32 = tmp31 * tmp7
    tmp33 = tmp28 + tmp32
    tmp34 = tmp33.to(tl.float32)
    tmp35 = tmp24 * tmp34
    tmp36 = tl.broadcast_to(tmp35, [RBLOCK])
    tmp38 = triton_helpers.promote_to_tensor(tl.sum(tmp36, 0))
    tmp40 = tmp24 * tmp39
    tmp41 = -0.5
    tmp42 = tmp38 * tmp41
    tmp43 = tmp39 * tmp39
    tmp44 = tmp43 * tmp39
    tmp45 = tmp42 * tmp44
    tmp46 = 0.00390625
    tmp47 = tmp45 * tmp46
    tmp48 = 2.0
    tmp49 = tmp34 * tmp48
    tmp50 = tmp47 * tmp49
    tmp51 = tmp40 + tmp50
    tmp54 = tmp52 + tmp53
    tmp57 = tmp56.to(tl.float32)
    tmp58 = tmp54 * tmp57
    tmp62 = tmp61.to(tl.float32)
    tmp63 = tmp59 * tmp62
    tmp64 = tmp58 + tmp63
    tmp67 = tmp66.to(tl.float32)
    tmp68 = tmp2 * tmp67
    tmp69 = tmp64 + tmp68
    tmp71 = tmp51.to(tl.float32)
    tmp72 = tmp70 + tmp71
    tmp73 = tmp72 * tmp31
    tmp74 = tmp69 + tmp73
    tmp75 = tmp72 * tmp7
    tmp76 = tmp75.to(tl.float32)
    tmp77 = tl.broadcast_to(tmp76, [RBLOCK])
    tmp79 = triton_helpers.promote_to_tensor(tl.sum(tmp77, 0))
    tmp80 = tmp72 * tmp27
    tmp81 = tmp74 + tmp80
    tmp82 = tmp81.to(tl.float32)
    tmp83 = tmp82 * tmp4
    tmp84 = tl.broadcast_to(tmp83, [RBLOCK])
    tmp86 = triton_helpers.promote_to_tensor(tl.sum(tmp84, 0))
    tmp88 = tl.full([1], -1, tl.int64)
    tmp89 = tmp87 == tmp88
    tmp92 = tl.sigmoid(tmp91)
    tmp93 = tmp92 * tmp48
    tmp94 = tmp90 * tmp93
    tmp95 = tmp94.to(tl.float32)
    tmp96 = 0.0
    tmp97 = tl.where(tmp89, tmp96, tmp95)
    tmp98 = tmp82 * tmp5
    tmp99 = tmp86 * tmp41
    tmp100 = tmp5 * tmp5
    tmp101 = tmp100 * tmp5
    tmp102 = tmp99 * tmp101
    tmp103 = tmp102 * tmp46
    tmp104 = tmp4 * tmp48
    tmp105 = tmp103 * tmp104
    tmp106 = tmp98 + tmp105
    tmp107 = tl.where(tmp89, tmp96, tmp106)
    tl.store(out_ptr6 + (r1 + 256*x0), tmp97, None)
    tl.store(out_ptr7 + (r1 + 256*x0), tmp107, None)
    tl.store(out_ptr0 + (x0), tmp12, None)
    tl.store(out_ptr1 + (x0), tmp18, None)
    tl.store(out_ptr4 + (x0), tmp79, None)
