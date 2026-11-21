
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.pointwise(
    size_hints={'x': 8388608}, 
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*bf16', 'in_ptr1': '*fp32', 'in_ptr2': '*fp32', 'in_ptr3': '*bf16', 'in_ptr4': '*bf16', 'in_ptr5': '*bf16', 'in_ptr6': '*bf16', 'in_ptr7': '*fp32', 'in_ptr8': '*fp32', 'in_ptr9': '*bf16', 'out_ptr0': '*bf16', 'out_ptr1': '*bf16', 'out_ptr2': '*bf16', 'out_ptr3': '*bf16', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_add_mul_neg_8', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 14, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_add_mul_neg_8(in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, in_ptr5, in_ptr6, in_ptr7, in_ptr8, in_ptr9, out_ptr0, out_ptr1, out_ptr2, out_ptr3, xnumel, XBLOCK : tl.constexpr):
    xnumel = 6291456
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = (xindex % 64)
    x4 = xindex // 64
    x2 = ((xindex // 192) % 2048)
    x5 = xindex
    tmp0 = tl.load(in_ptr0 + (64 + x0 + 128*x4), None).to(tl.float32)
    tmp2 = tl.load(in_ptr1 + (x4), None, eviction_policy='evict_last')
    tmp4 = tl.load(in_ptr2 + (x4), None, eviction_policy='evict_last')
    tmp12 = tl.load(in_ptr3 + (64 + x0 + 128*x4), None).to(tl.float32)
    tmp19 = tl.load(in_ptr4 + (x0 + 64*x2), None, eviction_policy='evict_last').to(tl.float32)
    tmp21 = tl.load(in_ptr0 + (x0 + 128*x4), None).to(tl.float32)
    tmp24 = tl.load(in_ptr3 + (x0 + 128*x4), None).to(tl.float32)
    tmp30 = tl.load(in_ptr5 + (x0 + 64*x2), None, eviction_policy='evict_last').to(tl.float32)
    tmp37 = tl.load(in_ptr6 + (64 + x0 + 128*x4), None).to(tl.float32)
    tmp39 = tl.load(in_ptr7 + (x4), None, eviction_policy='evict_last')
    tmp41 = tl.load(in_ptr8 + (x4), None, eviction_policy='evict_last')
    tmp47 = tl.load(in_ptr9 + (64 + x0 + 128*x4), None).to(tl.float32)
    tmp54 = tl.load(in_ptr6 + (x0 + 128*x4), None).to(tl.float32)
    tmp57 = tl.load(in_ptr9 + (x0 + 128*x4), None).to(tl.float32)
    tmp1 = tmp0.to(tl.float32)
    tmp3 = tmp1 * tmp2
    tmp5 = -0.5
    tmp6 = tmp4 * tmp5
    tmp7 = tmp2 * tmp2
    tmp8 = tmp7 * tmp2
    tmp9 = tmp6 * tmp8
    tmp10 = 0.0078125
    tmp11 = tmp9 * tmp10
    tmp13 = tmp12.to(tl.float32)
    tmp14 = 2.0
    tmp15 = tmp13 * tmp14
    tmp16 = tmp11 * tmp15
    tmp17 = tmp3 + tmp16
    tmp18 = tmp17.to(tl.float32)
    tmp20 = tmp18 * tmp19
    tmp22 = tmp21.to(tl.float32)
    tmp23 = tmp22 * tmp2
    tmp25 = tmp24.to(tl.float32)
    tmp26 = tmp25 * tmp14
    tmp27 = tmp11 * tmp26
    tmp28 = tmp23 + tmp27
    tmp29 = tmp28.to(tl.float32)
    tmp31 = tmp29 * tmp30
    tmp32 = tmp20 + tmp31
    tmp33 = -tmp30
    tmp34 = tmp18 * tmp33
    tmp35 = tmp29 * tmp19
    tmp36 = tmp34 + tmp35
    tmp38 = tmp37.to(tl.float32)
    tmp40 = tmp38 * tmp39
    tmp42 = tmp41 * tmp5
    tmp43 = tmp39 * tmp39
    tmp44 = tmp43 * tmp39
    tmp45 = tmp42 * tmp44
    tmp46 = tmp45 * tmp10
    tmp48 = tmp47.to(tl.float32)
    tmp49 = tmp48 * tmp14
    tmp50 = tmp46 * tmp49
    tmp51 = tmp40 + tmp50
    tmp52 = tmp51.to(tl.float32)
    tmp53 = tmp52 * tmp19
    tmp55 = tmp54.to(tl.float32)
    tmp56 = tmp55 * tmp39
    tmp58 = tmp57.to(tl.float32)
    tmp59 = tmp58 * tmp14
    tmp60 = tmp46 * tmp59
    tmp61 = tmp56 + tmp60
    tmp62 = tmp61.to(tl.float32)
    tmp63 = tmp62 * tmp30
    tmp64 = tmp53 + tmp63
    tmp65 = tmp52 * tmp33
    tmp66 = tmp62 * tmp19
    tmp67 = tmp65 + tmp66
    tl.store(out_ptr0 + (x5), tmp32, None)
    tl.store(out_ptr1 + (x5), tmp36, None)
    tl.store(out_ptr2 + (x5), tmp64, None)
    tl.store(out_ptr3 + (x5), tmp67, None)
