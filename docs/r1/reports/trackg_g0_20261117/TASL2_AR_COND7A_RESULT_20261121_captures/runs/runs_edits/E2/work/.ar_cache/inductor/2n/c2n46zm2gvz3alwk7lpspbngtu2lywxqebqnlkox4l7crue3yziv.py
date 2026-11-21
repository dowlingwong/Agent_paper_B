
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
    triton_meta={'signature': {'in_out_ptr0': '*fp32', 'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'in_ptr3': '*fp32', 'in_ptr4': '*bf16', 'in_ptr5': '*bf16', 'in_ptr6': '*bf16', 'in_ptr7': '*bf16', 'in_ptr8': '*fp32', 'in_ptr9': '*fp32', 'in_ptr10': '*fp32', 'in_ptr11': '*bf16', 'in_ptr12': '*bf16', 'in_ptr13': '*i64', 'in_ptr14': '*bf16', 'in_ptr15': '*bf16', 'out_ptr0': '*fp32', 'out_ptr1': '*fp32', 'out_ptr4': '*fp32', 'out_ptr6': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_div_embedding_dense_backward_mul_nll_loss_forward_pow_sum_24', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': True, 'num_load': 17, 'num_reduction': 5, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_div_embedding_dense_backward_mul_nll_loss_forward_pow_sum_24(in_out_ptr0, in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, in_ptr5, in_ptr6, in_ptr7, in_ptr8, in_ptr9, in_ptr10, in_ptr11, in_ptr12, in_ptr13, in_ptr14, in_ptr15, out_ptr0, out_ptr1, out_ptr4, out_ptr6, xnumel, rnumel):
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
    tmp0 = tl.load(in_ptr0 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp1 = tl.load(in_ptr1 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp3 = tl.load(in_ptr2 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp5 = tl.load(in_ptr3 + (x0), None, eviction_policy='evict_last')
    tmp14 = tl.load(in_ptr4 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp21 = tl.load(in_ptr5 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp22 = tl.load(in_ptr6 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp24 = tl.load(in_ptr7 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp27 = tl.load(in_ptr8 + (0))
    tmp28 = tl.broadcast_to(tmp27, [RBLOCK])
    tmp31 = tl.load(in_ptr9 + (0))
    tmp32 = tl.broadcast_to(tmp31, [RBLOCK])
    tmp42 = tl.load(in_ptr10 + (x0), None, eviction_policy='evict_last')
    tmp55 = tl.load(in_ptr11 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp56 = tl.load(in_ptr9 + (1))
    tmp57 = tl.broadcast_to(tmp56, [RBLOCK])
    tmp61 = tl.load(in_ptr12 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp80 = tl.load(in_ptr13 + (x0), None, eviction_policy='evict_last')
    tmp83 = tl.load(in_ptr14 + (r1 + 384*x0), rmask, other=0.0).to(tl.float32)
    tmp84 = tl.load(in_ptr15 + (3*x0 + (r1 // 128)), rmask, eviction_policy='evict_last', other=0.0).to(tl.float32)
    tmp2 = tmp0 + tmp1
    tmp4 = tmp3.to(tl.float32)
    tmp6 = tmp4 * tmp5
    tmp7 = tmp6.to(tl.float32)
    tmp8 = tmp2 * tmp7
    tmp9 = tmp8.to(tl.float32)
    tmp10 = tl.broadcast_to(tmp9, [RBLOCK])
    tmp12 = tl.where(rmask, tmp10, 0)
    tmp13 = triton_helpers.promote_to_tensor(tl.sum(tmp12, 0))
    tmp15 = tmp2 * tmp14
    tmp16 = tmp15.to(tl.float32)
    tmp17 = tl.broadcast_to(tmp16, [RBLOCK])
    tmp19 = tl.where(rmask, tmp17, 0)
    tmp20 = triton_helpers.promote_to_tensor(tl.sum(tmp19, 0))
    tmp23 = tmp21 + tmp22
    tmp25 = tmp23 + tmp24
    tmp26 = tmp25.to(tl.float32)
    tmp29 = tmp28.to(tl.float32)
    tmp30 = tmp29 * tmp7
    tmp33 = tmp32.to(tl.float32)
    tmp34 = tmp33 * tmp7
    tmp35 = tmp30 + tmp34
    tmp36 = tmp35.to(tl.float32)
    tmp37 = tmp26 * tmp36
    tmp38 = tl.broadcast_to(tmp37, [RBLOCK])
    tmp40 = tl.where(rmask, tmp38, 0)
    tmp41 = triton_helpers.promote_to_tensor(tl.sum(tmp40, 0))
    tmp43 = tmp26 * tmp42
    tmp44 = -0.5
    tmp45 = tmp41 * tmp44
    tmp46 = tmp42 * tmp42
    tmp47 = tmp46 * tmp42
    tmp48 = tmp45 * tmp47
    tmp49 = 0.0026041666666666665
    tmp50 = tmp48 * tmp49
    tmp51 = 2.0
    tmp52 = tmp36 * tmp51
    tmp53 = tmp50 * tmp52
    tmp54 = tmp43 + tmp53
    tmp58 = tmp57.to(tl.float32)
    tmp59 = tmp2 * tmp58
    tmp60 = tmp55 + tmp59
    tmp62 = tmp54.to(tl.float32)
    tmp63 = tmp61 + tmp62
    tmp64 = tmp63 * tmp33
    tmp65 = tmp60 + tmp64
    tmp66 = tmp63 * tmp29
    tmp67 = tmp65 + tmp66
    tmp68 = tmp67.to(tl.float32)
    tmp69 = tmp63 * tmp7
    tmp70 = tmp69.to(tl.float32)
    tmp71 = tl.broadcast_to(tmp70, [RBLOCK])
    tmp73 = tl.where(rmask, tmp71, 0)
    tmp74 = triton_helpers.promote_to_tensor(tl.sum(tmp73, 0))
    tmp75 = tmp68 * tmp4
    tmp76 = tl.broadcast_to(tmp75, [RBLOCK])
    tmp78 = tl.where(rmask, tmp76, 0)
    tmp79 = triton_helpers.promote_to_tensor(tl.sum(tmp78, 0))
    tmp81 = tl.full([1], -1, tl.int64)
    tmp82 = tmp80 == tmp81
    tmp85 = tl.sigmoid(tmp84)
    tmp86 = tmp85 * tmp51
    tmp87 = tmp83 * tmp86
    tmp88 = tmp87.to(tl.float32)
    tmp89 = 0.0
    tmp90 = tl.where(tmp82, tmp89, tmp88)
    tmp91 = tmp68 * tmp5
    tmp92 = tmp79 * tmp44
    tmp93 = tmp5 * tmp5
    tmp94 = tmp93 * tmp5
    tmp95 = tmp92 * tmp94
    tmp96 = tmp95 * tmp49
    tmp97 = tmp4 * tmp51
    tmp98 = tmp96 * tmp97
    tmp99 = tmp91 + tmp98
    tmp100 = tl.where(tmp82, tmp89, tmp99)
    tl.store(out_ptr6 + (r1 + 384*x0), tmp90, rmask)
    tl.store(in_out_ptr0 + (r1 + 384*x0), tmp100, rmask)
    tl.store(out_ptr0 + (x0), tmp13, None)
    tl.store(out_ptr1 + (x0), tmp20, None)
    tl.store(out_ptr4 + (x0), tmp74, None)
