# AOT ID: ['1_inference']
from ctypes import c_void_p, c_long, c_int
import torch
import math
import random
import os
import tempfile
from math import inf, nan
from torch._inductor.hooks import run_intermediate_hooks
from torch._inductor.utils import maybe_profile
from torch._inductor.codegen.memory_planning import _align as align
from torch import device, empty_strided
from torch._inductor.async_compile import AsyncCompile
from torch._inductor.select_algorithm import extern_kernels
from torch._inductor.codegen.multi_kernel import MultiKernelCall
import triton
import triton.language as tl
from torch._inductor.runtime.triton_heuristics import (
    grid,
    split_scan_grid,
    grid_combo_kernels,
    start_graph,
    end_graph,
    cooperative_reduction_grid,
)
from torch._C import _cuda_getCurrentRawStream as get_raw_stream
from torch._C import _cuda_getCurrentRawStream as get_raw_stream

aten = torch.ops.aten
inductor_ops = torch.ops.inductor
_quantized = torch.ops._quantized
assert_size_stride = torch._C._dynamo.guards.assert_size_stride
empty_strided_cpu = torch._C._dynamo.guards._empty_strided_cpu
empty_strided_cuda = torch._C._dynamo.guards._empty_strided_cuda
empty_strided_xpu = torch._C._dynamo.guards._empty_strided_xpu
reinterpret_tensor = torch._C._dynamo.guards._reinterpret_tensor
alloc_from_pool = torch.ops.inductor._alloc_from_pool
async_compile = AsyncCompile()
empty_strided_p2p = torch._C._distributed_c10d._SymmetricMemory.empty_strided_p2p


# kernel path: /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs/runs_smoke/s002/work/.ar_cache/inductor/7e/c7edt7jloxfnt7y32dulosya7agd2zrq5kdw4erryxucfgzbqq4n.py
# Topologically Sorted Source Nodes: [mul, sub, mul_, sub_1, lerp_, sub_2, lerp__1, square, pow_2, bias2, truediv, sqrt, denom, truediv_2, pow_1, bias1, step_size, neg, mul_1, add_], Original ATen: [aten.mul, aten.rsub, aten.lerp, aten.pow, aten.div, aten.sqrt, aten.add, aten.neg]
# Source node to ATen node mapping:
#   add_ => add_3
#   bias1 => sub_7
#   bias2 => sub_8
#   denom => add_2
#   lerp_ => abs_1, add, ge, mul_2, sub_2, sub_3, where, where_1
#   lerp__1 => abs_2, add_1, ge_1, mul_3, sub_5, sub_6, where_2, where_3
#   mul => mul
#   mul_ => mul_1
#   mul_1 => mul_4
#   neg => neg
#   pow_1 => pow_2
#   pow_2 => pow_3
#   sqrt => sqrt
#   square => pow_1
#   step_size => div_1
#   sub => sub
#   sub_1 => sub_1
#   sub_2 => sub_4
#   truediv => div
#   truediv_2 => div_2
# Graph fragment:
#   %mul : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%device_put_1, %device_put_5), kwargs = {})
#   %sub : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (1, %mul), kwargs = {})
#   %mul_1 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%arg1_1, %sub), kwargs = {})
#   %sub_1 : [num_users=3] = call_function[target=torch.ops.aten.sub.Tensor](args = (1, %device_put_2), kwargs = {})
#   %abs_1 : [num_users=1] = call_function[target=torch.ops.aten.abs.default](args = (%sub_1,), kwargs = {})
#   %ge : [num_users=2] = call_function[target=torch.ops.aten.ge.Scalar](args = (%abs_1, 0.5), kwargs = {})
#   %sub_2 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (%sub_1, 1), kwargs = {})
#   %where : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%ge, %sub_2, %sub_1), kwargs = {})
#   %sub_3 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (%arg8_1, %arg7_1), kwargs = {})
#   %mul_2 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%where, %sub_3), kwargs = {})
#   %where_1 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%ge, %arg8_1, %arg7_1), kwargs = {})
#   %add : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_2, %where_1), kwargs = {})
#   %sub_4 : [num_users=3] = call_function[target=torch.ops.aten.sub.Tensor](args = (1, %device_put_3), kwargs = {})
#   %abs_2 : [num_users=1] = call_function[target=torch.ops.aten.abs.default](args = (%sub_4,), kwargs = {})
#   %ge_1 : [num_users=2] = call_function[target=torch.ops.aten.ge.Scalar](args = (%abs_2, 0.5), kwargs = {})
#   %sub_5 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (%sub_4, 1), kwargs = {})
#   %where_2 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%ge_1, %sub_5, %sub_4), kwargs = {})
#   %pow_1 : [num_users=2] = call_function[target=torch.ops.aten.pow.Tensor_Scalar](args = (%arg8_1, 2), kwargs = {})
#   %sub_6 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (%pow_1, %arg9_1), kwargs = {})
#   %mul_3 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%where_2, %sub_6), kwargs = {})
#   %where_3 : [num_users=1] = call_function[target=torch.ops.aten.where.self](args = (%ge_1, %pow_1, %arg9_1), kwargs = {})
#   %add_1 : [num_users=2] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_3, %where_3), kwargs = {})
#   %pow_3 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Tensor](args = (%device_put_3, %device_put), kwargs = {})
#   %sub_8 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (1, %pow_3), kwargs = {})
#   %div : [num_users=1] = call_function[target=torch.ops.aten.div.Tensor](args = (%add_1, %sub_8), kwargs = {})
#   %sqrt : [num_users=1] = call_function[target=torch.ops.aten.sqrt.default](args = (%div,), kwargs = {})
#   %add_2 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%sqrt, %device_put_4), kwargs = {})
#   %div_2 : [num_users=1] = call_function[target=torch.ops.aten.div.Tensor](args = (%add, %add_2), kwargs = {})
#   %pow_2 : [num_users=1] = call_function[target=torch.ops.aten.pow.Tensor_Tensor](args = (%device_put_2, %device_put), kwargs = {})
#   %sub_7 : [num_users=1] = call_function[target=torch.ops.aten.sub.Tensor](args = (1, %pow_2), kwargs = {})
#   %div_1 : [num_users=1] = call_function[target=torch.ops.aten.div.Tensor](args = (%device_put_1, %sub_7), kwargs = {})
#   %neg : [num_users=1] = call_function[target=torch.ops.aten.neg.default](args = (%div_1,), kwargs = {})
#   %mul_4 : [num_users=1] = call_function[target=torch.ops.aten.mul.Tensor](args = (%div_2, %neg), kwargs = {})
#   %add_3 : [num_users=1] = call_function[target=torch.ops.aten.add.Tensor](args = (%mul_1, %mul_4), kwargs = {})
#   %copy_ : [num_users=0] = call_function[target=torch.ops.aten.copy_.default](args = (%arg1_1, %add_3), kwargs = {})
#   %copy__1 : [num_users=0] = call_function[target=torch.ops.aten.copy_.default](args = (%arg7_1, %add), kwargs = {})
#   %copy__2 : [num_users=0] = call_function[target=torch.ops.aten.copy_.default](args = (%arg9_1, %add_1), kwargs = {})
triton_poi_fused_add_div_lerp_mul_neg_pow_rsub_sqrt_0 = async_compile.triton('triton_poi_fused_add_div_lerp_mul_neg_pow_rsub_sqrt_0', '''
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.pointwise(
    size_hints={'x': 2097152}, 
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*fp32', 'in_ptr1': '*fp32', 'in_ptr2': '*fp32', 'in_ptr3': '*fp32', 'in_ptr4': '*fp32', 'in_ptr5': '*fp32', 'in_ptr6': '*fp32', 'in_ptr7': '*fp32', 'in_ptr8': '*fp32', 'in_ptr9': '*fp32', 'out_ptr4': '*fp32', 'out_ptr5': '*fp32', 'out_ptr6': '*fp32', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_add_div_lerp_mul_neg_pow_rsub_sqrt_0', 'mutated_arg_names': ['in_ptr2', 'in_ptr4', 'in_ptr7', 'out_ptr4', 'out_ptr5', 'out_ptr6'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 10, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_add_div_lerp_mul_neg_pow_rsub_sqrt_0(in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, in_ptr5, in_ptr6, in_ptr7, in_ptr8, in_ptr9, out_ptr4, out_ptr5, out_ptr6, xnumel, XBLOCK : tl.constexpr):
    xnumel = 2097152
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = tl.full([XBLOCK], True, tl.int1)
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (0))
    tmp1 = tl.broadcast_to(tmp0, [XBLOCK])
    tmp9 = tl.load(in_ptr1 + (x0), None)
    tmp10 = tl.load(in_ptr2 + (x0), None)
    tmp15 = tl.load(in_ptr3 + (0))
    tmp16 = tl.broadcast_to(tmp15, [XBLOCK])
    tmp23 = tl.load(in_ptr4 + (x0), None)
    tmp28 = tl.load(in_ptr5 + (0))
    tmp29 = tl.broadcast_to(tmp28, [XBLOCK])
    tmp34 = tl.load(in_ptr6 + (0))
    tmp35 = tl.broadcast_to(tmp34, [XBLOCK])
    tmp38 = tl.load(in_ptr7 + (x0), None)
    tmp39 = tl.load(in_ptr8 + (0))
    tmp40 = tl.broadcast_to(tmp39, [XBLOCK])
    tmp41 = tl.load(in_ptr9 + (0))
    tmp42 = tl.broadcast_to(tmp41, [XBLOCK])
    tmp2 = 1.0
    tmp3 = tmp2 - tmp1
    tmp4 = tl_math.abs(tmp3)
    tmp5 = 0.5
    tmp6 = tmp4 >= tmp5
    tmp7 = tmp3 - tmp2
    tmp8 = tl.where(tmp6, tmp7, tmp3)
    tmp11 = tmp9 - tmp10
    tmp12 = tmp8 * tmp11
    tmp13 = tl.where(tmp6, tmp9, tmp10)
    tmp14 = tmp12 + tmp13
    tmp17 = tmp2 - tmp16
    tmp18 = tl_math.abs(tmp17)
    tmp19 = tmp18 >= tmp5
    tmp20 = tmp17 - tmp2
    tmp21 = tl.where(tmp19, tmp20, tmp17)
    tmp22 = tmp9 * tmp9
    tmp24 = tmp22 - tmp23
    tmp25 = tmp21 * tmp24
    tmp26 = tl.where(tmp19, tmp22, tmp23)
    tmp27 = tmp25 + tmp26
    tmp30 = libdevice.pow(tmp16, tmp29)
    tmp31 = tmp2 - tmp30
    tmp32 = tmp27 / tmp31
    tmp33 = libdevice.sqrt(tmp32)
    tmp36 = tmp33 + tmp35
    tmp37 = tmp14 / tmp36
    tmp43 = tmp40 * tmp42
    tmp44 = tmp2 - tmp43
    tmp45 = tmp38 * tmp44
    tmp46 = libdevice.pow(tmp1, tmp29)
    tmp47 = tmp2 - tmp46
    tmp48 = tmp40 / tmp47
    tmp49 = -tmp48
    tmp50 = tmp37 * tmp49
    tmp51 = tmp45 + tmp50
    tl.store(out_ptr4 + (x0), tmp14, None)
    tl.store(out_ptr5 + (x0), tmp27, None)
    tl.store(out_ptr6 + (x0), tmp51, None)
''', device_str='cuda')


async_compile.wait(globals())
del async_compile

def call(args):
    arg0_1, arg1_1, arg2_1, arg3_1, arg4_1, arg5_1, arg6_1, arg7_1, arg8_1, arg9_1 = args
    args.clear()
    assert_size_stride(arg0_1, (), ())
    assert_size_stride(arg1_1, (8192, 256), (256, 1))
    assert_size_stride(arg2_1, (), ())
    assert_size_stride(arg3_1, (), ())
    assert_size_stride(arg4_1, (), ())
    assert_size_stride(arg5_1, (), ())
    assert_size_stride(arg6_1, (), ())
    assert_size_stride(arg7_1, (8192, 256), (256, 1))
    assert_size_stride(arg8_1, (8192, 256), (256, 1))
    assert_size_stride(arg9_1, (8192, 256), (256, 1))
    with torch.cuda._DeviceGuard(0):
        torch.cuda.set_device(0)
        buf0 = empty_strided_cuda((), (), torch.float32)
        buf0.copy_(arg2_1, False)
        del arg2_1
        buf1 = empty_strided_cuda((), (), torch.float32)
        buf1.copy_(arg6_1, False)
        del arg6_1
        buf2 = empty_strided_cuda((), (), torch.float32)
        buf2.copy_(arg3_1, False)
        del arg3_1
        buf3 = empty_strided_cuda((), (), torch.float32)
        buf3.copy_(arg4_1, False)
        del arg4_1
        buf4 = empty_strided_cuda((), (), torch.float32)
        buf4.copy_(arg0_1, False)
        del arg0_1
        buf5 = empty_strided_cuda((), (), torch.float32)
        buf5.copy_(arg5_1, False)
        del arg5_1
        # Topologically Sorted Source Nodes: [mul, sub, mul_, sub_1, lerp_, sub_2, lerp__1, square, pow_2, bias2, truediv, sqrt, denom, truediv_2, pow_1, bias1, step_size, neg, mul_1, add_], Original ATen: [aten.mul, aten.rsub, aten.lerp, aten.pow, aten.div, aten.sqrt, aten.add, aten.neg]
        stream0 = get_raw_stream(0)
        triton_poi_fused_add_div_lerp_mul_neg_pow_rsub_sqrt_0.run(buf2, arg8_1, arg7_1, buf3, arg9_1, buf4, buf5, arg1_1, buf0, buf1, arg7_1, arg9_1, arg1_1, 2097152, grid=grid(2097152), stream=stream0)
        del arg1_1
        del arg7_1
        del arg8_1
        del arg9_1
        del buf0
        del buf1
        del buf2
        del buf3
        del buf4
        del buf5
    return ()


def benchmark_compiled_module(times=10, repeat=10):
    from torch._dynamo.testing import rand_strided
    from torch._inductor.utils import print_performance
    arg0_1 = rand_strided((), (), device='cpu', dtype=torch.float32)
    arg1_1 = rand_strided((8192, 256), (256, 1), device='cuda:0', dtype=torch.float32)
    arg2_1 = rand_strided((), (), device='cpu', dtype=torch.float32)
    arg3_1 = rand_strided((), (), device='cpu', dtype=torch.float32)
    arg4_1 = rand_strided((), (), device='cpu', dtype=torch.float32)
    arg5_1 = rand_strided((), (), device='cpu', dtype=torch.float32)
    arg6_1 = rand_strided((), (), device='cpu', dtype=torch.float32)
    arg7_1 = rand_strided((8192, 256), (256, 1), device='cuda:0', dtype=torch.float32)
    arg8_1 = rand_strided((8192, 256), (256, 1), device='cuda:0', dtype=torch.float32)
    arg9_1 = rand_strided((8192, 256), (256, 1), device='cuda:0', dtype=torch.float32)
    fn = lambda: call([arg0_1, arg1_1, arg2_1, arg3_1, arg4_1, arg5_1, arg6_1, arg7_1, arg8_1, arg9_1])
    return print_performance(fn, times=times, repeat=repeat)


if __name__ == "__main__":
    from torch._inductor.wrapper_benchmark import compiled_module_main
    compiled_module_main('None', benchmark_compiled_module)
