# Copyright 2020 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0(the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http:  // www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================

"""Operators for quantization."""

from ..._checkparam import ParamValidator as validator
from ..._checkparam import Rel, check_bool, check_int_positive, check_int
from ..primitive import PrimitiveWithInfer, prim_attr_register
from ...common import dtype as mstype

__all__ = ["FakeQuantWithMinMax",
           "FakeQuantWithMinMaxGrad",
           "FakeQuantWithMinMaxPerChannel",
           "FakeQuantWithMinMaxPerChannelGrad",
           "BatchNormFold",
           "BatchNormFoldGrad",
           "CorrectionMul",
           "CorrectionMulGrad",
           "BatchNormFold2",
           "BatchNormFold2Grad",
           ]


class FakeQuantWithMinMax(PrimitiveWithInfer):
    r"""
    Simulate the quantize and dequantize operations in training time.

    Args:
        num_bits (int) : Number bits for aware quantilization. Default: 8.
        ema (bool): Use EMA algorithm update value min and max. Default: False.
        ema_decay (int) : EMA algorithm decay parameter. Default: 0.999.
        quant_delay (int): Quantilization delay parameter. Before delay step in training time not update
            simulate aware quantize funcion. After delay step in training time begin simulate the aware
            quantize funcion. Default: 0.
        symmetric (bool): Quantization algorithm use symmetric or not. Default: False.
        narrow_range (bool): Quantization algorithm use narrow range or not. Default: False.
        training (bool): Training the network or not. Default: True.

    Inputs:
        - **x** (Tensor) : float32 Tensor representing the shape of the output tensor.
        - **min** (Tensor) : Value of the min range of the input data x.
        - **max** (Tensor) : Value of the max range of the input data x.

    Outputs:
        - Tensor: Simulate quantize tensor of x.

    Examples:
        >>> input_tensor = Tensor(np.random.rand(3, 16, 5, 5), mstype.float32)
        >>> min_tensor = Tensor(np.array([-6]), mstype.float32)
        >>> max_tensor = Tensor(np.array([6]), mstype.float32)
        >>> output_tensor = P.FakeQuantWithMinMax(num_bits=8)(input_tensor, min_tensor, max_tensor)
    """
    support_quant_bit = [4, 7, 8]

    @prim_attr_register
    def __init__(self, num_bits=8, ema=False, ema_decay=0.999, quant_delay=0, symmetric=False, narrow_range=False,
                 training=True):
        """init FakeQuantWithMinMax OP"""
        if num_bits not in self.support_quant_bit:
            raise ValueError("Attr \'num_bits\' is not support.")
        if ema and not ema_decay:
            raise ValueError(
                "Attr \'ema\' and \'ema_decay\' should set together.")

        self.ema = check_bool(ema)
        self.symmetric = check_bool(symmetric)
        self.narrow_range = check_bool(narrow_range)
        self.training = check_bool(training)
        self.ema_decay = validator.check_number_range(
            'ema_decay', ema_decay, 0, 1, Rel.INC_BOTH)
        self.num_bits = check_int_positive(num_bits)
        self.quant_delay = check_int(quant_delay)
        self.init_prim_io_names(inputs=['x', 'min', 'max'],
                                outputs=['out'])

    def infer_shape(self, x_shape, min_shape, max_shape):
        validator.check_integer("x shape", len(x_shape), 1, Rel.GT)
        validator.check("min shape", min_shape, "max shape", max_shape)
        validator.check_integer("min shape", len(min_shape), 1, Rel.EQ)
        validator.check_integer("max shape", len(min_shape), 1, Rel.EQ)
        return x_shape

    def infer_dtype(self, x_type, min_type, max_type):
        validator.check_typename(
            "x type", x_type, (mstype.float16, mstype.float32))
        validator.check_typename("min type", min_type,
                                 (mstype.float16, mstype.float32))
        validator.check_typename("max type", max_type,
                                 (mstype.float16, mstype.float32))
        return x_type


class FakeQuantWithMinMaxGrad(PrimitiveWithInfer):
    """Performs grad of FakeQuantWithMinMax operation."""
    support_quant_bit = [4, 8]

    @prim_attr_register
    def __init__(self, num_bits=8, quant_delay=0):
        if num_bits not in self.support_quant_bit:
            raise ValueError("Attr \'num_bits\' is not support.")

        self.quant_delay = check_int(quant_delay)
        self.num_bits = check_int_positive(num_bits)
        self.init_prim_io_names(inputs=['dout', 'x', 'min', 'max'],
                                outputs=['dx'])

    def infer_shape(self, dout_shape, x_shape, min_shape, max_shape):
        validator.check("dout shape", dout_shape, "x shape", x_shape)
        validator.check("min shape", min_shape, "max shape", max_shape)
        validator.check_integer("min shape", len(min_shape), 1, Rel.EQ)
        validator.check_integer("max shape", len(min_shape), 1, Rel.EQ)
        return dout_shape

    def infer_dtype(self, dout_type, x_type, min_type, max_type):
        validator.check_typename(
            "dout type", dout_type, (mstype.float16, mstype.float32))
        validator.check_typename(
            "x type", x_type, (mstype.float16, mstype.float32))
        validator.check_typename("min type", min_type,
                                 (mstype.float16, mstype.float32))
        validator.check_typename("max type", max_type,
                                 (mstype.float16, mstype.float32))
        return dout_type


class FakeQuantWithMinMaxPerChannel(PrimitiveWithInfer):
    r"""
    Simulate the quantize and dequantize operations in training time base on per channel.

    Args:
        num_bits (int) : Number bits to quantilization. Default: 8.
        ema (bool): Use EMA algorithm update tensor min and tensor max. Default: False.
        ema_decay (int) : EMA algorithm decay parameter. Default: 0.999.
        quant_delay (int): Quantilization delay  parameter. Before delay step in training time not
            update the weight data to simulate quantize operation. After delay step in training time
            begin simulate the quantize operation. Default: 0.
        symmetric (bool): Quantization algorithm use symmetric or not. Default: False.
        narrow_range (bool): Quantization algorithm use narrow range or not. Default: False.
        training (bool): Training the network or not. Default: True.

    Inputs:
        - **x** (Tensor) : 4-D float32 Tensor representing the shape of the output tensor.
        - **min** (int, float) : Value of the min range of the input data.
        - **max** (int, float) : Value of the max range of the input data.

    Outputs:
        - Tensor, has the same type as input.

    Examples:
        >>> input_tensor = Tensor(np.random.rand(3,4,5,5), mstype.float32)
        >>> min_tensor = Tensor(np.array([-6.0, -6.5, -4.0, -5.0]), mstype.float32)
        >>> max_tensor = Tensor(np.array([6.0, 6.5, 4.0, 5.0]), mstype.float32)
        >>> output_tensor = P.FakeQuantWithMinMax(num_bits=8)(input_tensor, min_tensor, max_tensor)
    """
    support_quant_bit = [4, 8]
    channel_idx = 0

    @prim_attr_register
    def __init__(self, num_bits=8, ema=False, ema_decay=0.999, quant_delay=0, symmetric=False, narrow_range=False,
                 training=True):
        """init FakeQuantWithMinMaxPerChannel OP"""
        if num_bits not in self.support_quant_bit:
            raise ValueError("Attr \'num_bits\' is not support.")
        if ema and not ema_decay:
            raise ValueError(
                "Attr \'ema\' and \'ema_decay\' should set together.")

        self.ema = check_bool(ema)
        self.symmetric = check_bool(symmetric)
        self.narrow_range = check_bool(narrow_range)
        self.training = check_bool(training)
        self.ema_decay = validator.check_number_range(
            'ema_decay', ema_decay, 0, 1, Rel.INC_BOTH)
        self.num_bits = check_int_positive(num_bits)
        self.quant_delay = check_int(quant_delay)
        self.init_prim_io_names(inputs=['x', 'min', 'max'],
                                outputs=['out'])

    def infer_shape(self, x_shape, min_shape, max_shape):
        validator.check_integer("x shape", len(x_shape), 1, Rel.GT)
        validator.check_integer(
            "min len", min_shape[0], x_shape[self.channel_idx], Rel.EQ)
        validator.check_integer(
            "max len", max_shape[0], x_shape[self.channel_idx], Rel.EQ)
        return x_shape

    def infer_dtype(self, x_type, min_type, max_type):
        validator.check_typename(
            "x type", x_type, (mstype.float16, mstype.float32))
        validator.check_typename("min type", min_type,
                                 (mstype.float16, mstype.float32))
        validator.check_typename("max type", max_type,
                                 (mstype.float16, mstype.float32))
        return x_type


class FakeQuantWithMinMaxPerChannelGrad(PrimitiveWithInfer):
    """Performs grad of FakeQuantWithMinMaxPerChannel operation."""
    support_quant_bit = [4, 8]

    @prim_attr_register
    def __init__(self, num_bits=8, quant_delay=0):
        """init FakeQuantWithMinMaxPerChannel Fill"""
        if num_bits not in self.support_quant_bit:
            raise ValueError("Attr \'num_bits\' is not support.")

        self.quant_delay = check_int(quant_delay)
        self.num_bits = check_int_positive(num_bits)
        self.init_prim_io_names(inputs=['dout', 'x', 'min', 'max'],
                                outputs=['dx'])

    def infer_shape(self, dout_shape, x_shape, min_shape, max_shape):
        validator.check("dout shape", dout_shape, "x shape", x_shape)
        validator.check("min shape", min_shape, "max shape", max_shape)
        return dout_shape

    def infer_dtype(self, dout_type, x_type, min_type, max_type):
        validator.check_typename(
            "dout", dout_type, (mstype.float16, mstype.float32))
        validator.check_typename("x", x_type, (mstype.float16, mstype.float32))
        validator.check_typename(
            "min", min_type, (mstype.float16, mstype.float32))
        validator.check_typename(
            "max", max_type, (mstype.float16, mstype.float32))
        return dout_type


class BatchNormFold(PrimitiveWithInfer):
    """
    Batch normalization folded.

    Args:
        momentum (float): Momentum value should be [0, 1]. Default: 0.1.
        epsilon (float): A small float number to avoid dividing by 0. 1e-12 if dtype in
            float32 else 1e-3. Default: 1e-12.
        is_training (bool): In training mode set True, else set False. Default: True.
        freeze_bn (int): Delay in steps at which computation switches from regular batch
            norm to frozen mean and std. Default: 0.

    Inputs:
        - **x** (Tensor) - Tensor of shape :math:`(N, C)`.
        - **mean** (Tensor) - Tensor of shape :math:`(C,)`.
        - **variance** (Tensor) - Tensor of shape :math:`(C,)`.
        - **global_step** (Tensor) - Tensor to record current global step.

    Outputs:
        Tuple of 4 Tensor, the normalized input and the updated parameters.

        - **batch_mean** (Tensor) - Tensor of shape :math:`(C,)`.
        - **batch_std** (Tensor) - Tensor of shape :math:`(C,)`.
        - **running_mean** (Tensor) - Tensor of shape :math:`(C,)`.
        - **running_std** (Tensor) - Tensor of shape :math:`(C,)`.

    """
    channel = 1

    @prim_attr_register
    def __init__(self, momentum=0.1, epsilon=1e-12, is_training=True, freeze_bn=0):
        """init batch norm fold layer"""
        self.momentum = validator.check_number_range(
            'momentum', momentum, 0, 1, Rel.INC_BOTH)
        self.epsilon = validator.check_float_positive('epsilon', epsilon)
        self.is_training = check_bool(is_training)
        self.freeze_bn = check_int(freeze_bn)

        self.init_prim_io_names(inputs=['x', 'mean', 'variance', 'global_step'],
                                outputs=['batch_mean', 'batch_std', 'running_mean', 'running_std'])

    def infer_shape(self, x_shape, mean_shape, variance_shape, global_step_shape):
        validator.check("mean shape", mean_shape,
                        "gamma_shape", variance_shape)
        validator.check("mean_shape size",
                        mean_shape[0], "input channel", x_shape[self.channel])
        validator.check_integer("global_step shape",
                                len(global_step_shape), 1, Rel.EQ)
        return mean_shape, mean_shape, mean_shape, mean_shape

    def infer_dtype(self, x_type, mean_type, variance_type, global_step_type):
        validator.check("input type", x_type, "mean type", mean_type)
        validator.check("input type", x_type, "variance type", variance_type)
        validator.check_typename("input type", x_type,
                                 (mstype.float16, mstype.float32))
        validator.check_typename(
            "global_step type", global_step_type, (mstype.int32,))
        return x_type, x_type, x_type, x_type


class BatchNormFoldGrad(PrimitiveWithInfer):
    """Performs grad of BatchNormFold operation."""
    channel = 1

    @prim_attr_register
    def __init__(self, epsilon=1e-12, is_training=True, freeze_bn=0):
        """init BatchNormGrad layer"""
        self.is_training = check_bool(is_training)
        self.freeze_bn = check_int(freeze_bn)
        self.epsilon = validator.check_float_positive('epsilon', epsilon)
        self.init_prim_io_names(inputs=['d_batch_mean', 'd_batch_std', 'x', 'batch_mean', 'batch_std', 'global_step'],
                                outputs=['dx'])

    def infer_shape(self, d_batch_mean_shape, d_batch_std_shape, x_shape, batch_mean_shape, batch_std_shape,
                    global_step_shape):
        validator.check("d_batch_mean shape", d_batch_mean_shape,
                        "d_batch_std shape", d_batch_std_shape)
        validator.check("d_batch_mean shape", d_batch_mean_shape,
                        "batch_mean shape", batch_mean_shape)
        validator.check("d_batch_mean shape", d_batch_mean_shape,
                        "batch_std shape", batch_std_shape)
        validator.check(
            "x_shape shape", d_batch_mean_shape[0], "input channel", x_shape[self.channel])
        validator.check_integer("global_step shape",
                                len(global_step_shape), 1, Rel.EQ)
        return x_shape

    def infer_dtype(self, d_batch_mean_type, d_batch_std_type, x_type, batch_mean_type, batch_std_type,
                    global_step_type):
        validator.check("input type", x_type,
                        "d_batch_mean type", d_batch_mean_type)
        validator.check("input type", x_type,
                        "d_batch_std type", d_batch_std_type)
        validator.check("input type", x_type,
                        "batch_mean type", batch_mean_type)
        validator.check("input type", x_type, "batch_std type", batch_std_type)
        validator.check_typename("input type", x_type,
                                 (mstype.float16, mstype.float32))
        validator.check_typename(
            "global_step type", global_step_type, (mstype.int32,))
        return x_type


class CorrectionMul(PrimitiveWithInfer):
    """
    Scale the weights with a correction factor to the long term statistics
    prior to quantization. This ensures that there is no jitter in the quantized weights
    due to batch to batch variation.

    Inputs:
        - **x** (Tensor) - Tensor of shape :math:`(N, C)`.
        - **batch_std** (Tensor) - Tensor of shape :math:`(C,)`.
        - **running_std** (Tensor) - Tensor of shape :math:`(C,)`.

    Outputs:
        - **out** (Tensor) - Tensor has the same shape as x.

    """
    channel = 0

    @prim_attr_register
    def __init__(self):
        """init correction mul layer"""
        self.init_prim_io_names(inputs=['x', 'batch_std', 'running_std'],
                                outputs=['out'])

    def infer_shape(self, x_shape, batch_std_shape, running_std_shape):
        validator.check("batch_std shape", batch_std_shape,
                        "running_std shape", running_std_shape)
        validator.check(
            "batch_std size", batch_std_shape[0], "x_shape channel size", x_shape[self.channel])
        return x_shape

    def infer_dtype(self, x_type, batch_std_type, running_std_type):
        validator.check("batch_std type", batch_std_type,
                        "running_std type", running_std_type)
        validator.check("batch_std_type", batch_std_type, "x_type", x_type)
        validator.check_typename(
            "batch_std type", batch_std_type, (mstype.float16, mstype.float32))
        return x_type


class CorrectionMulGrad(PrimitiveWithInfer):
    """Performs grad of CorrectionMul operation."""
    channel = 0

    @prim_attr_register
    def __init__(self):
        """init correction mul layer"""
        self.init_prim_io_names(inputs=['dout', 'x', 'gamma', 'running_std'],
                                outputs=['dx', 'd_gamma'])

    def infer_shape(self, dout_shape, x_shape, gamma_shape, running_std_shape):
        validator.check("dout shape", dout_shape, "x_shape x", x_shape)
        validator.check(
            "gamma size", gamma_shape[0], "dout channel size", dout_shape[self.channel])
        validator.check(
            "running_std size", running_std_shape[0], "dout channel size", dout_shape[self.channel])
        return x_shape, gamma_shape

    def infer_dtype(self, dout_type, x_type, gamma_type, running_std_type):
        validator.check("x type", x_type, "dout type", dout_type)
        validator.check("gamma type", gamma_type, "dout type", dout_type)
        validator.check("running_std type", running_std_type,
                        "dout type", dout_type)
        validator.check_typename(
            "dout type", dout_type, (mstype.float16, mstype.float32))
        return x_type, x_type


class BatchNormFold2(PrimitiveWithInfer):
    """
    Scale the bias with a correction factor to the long term statistics
    prior to quantization. This ensures that there is no jitter in the quantized bias
    due to batch to batch variation.

    Inputs:
        - **x** (Tensor)  - Tensor of shape :math:`(N, C)`.
        - **beta** (Tensor) - Tensor of shape :math:`(C,)`.
        - **gamma** (Tensor) - Tensor of shape :math:`(C,)`.
        - **batch_std** (Tensor) - Tensor of shape :math:`(C,)`.
        - **batch_mean** (Tensor) - Tensor of shape :math:`(C,)`.
        - **running_std** (Tensor) - Tensor of shape :math:`(C,)`.
        - **running_mean** (Tensor) - Tensor of shape :math:`(C,)`.
        - **global_step** (Tensor) - Tensor to record current global step.

    Outputs:
        - **y** (Tensor) - Tensor has the same shape as x.

    """
    channel = 1

    @prim_attr_register
    def __init__(self, freeze_bn=0):
        """init conv2d fold layer"""
        self.freeze_bn = check_int(freeze_bn)
        self.init_prim_io_names(inputs=['x', 'beta', 'gamma', 'batch_std', 'batch_mean',
                                        'running_std', 'running_mean', 'global_step'],
                                outputs=['y'])

    def infer_shape(self, x_shape, beta_shape, gamma_shape, batch_std_shape, running_std_shape, batch_mean_shape,
                    running_mean_shape, global_step_shape):
        validator.check("batch_std shape", batch_std_shape,
                        "running_std shape", running_std_shape)
        validator.check("batch_std shape", batch_std_shape,
                        "batch_mean shape", batch_mean_shape)
        validator.check("batch_std shape", batch_std_shape,
                        "beta shape", beta_shape)
        validator.check("batch_std shape", batch_std_shape,
                        "running_mean shape", running_mean_shape)
        validator.check("batch_std shape", batch_std_shape,
                        "batch_mean shape", gamma_shape)
        validator.check(
            "batch_std size", batch_std_shape[0], "x_shape channel size", x_shape[self.channel])
        validator.check_integer("global_step shape",
                                len(global_step_shape), 1, Rel.EQ)
        return x_shape

    def infer_dtype(self, x_type, beta_type, gamma_type, batch_std_type, running_std_type, batch_mean_type,
                    running_mean_type, global_step_type):
        validator.check("batch_std type", batch_std_type,
                        "running_std type", running_std_type)
        validator.check("batch_std type", batch_std_type,
                        "batch_mean type", batch_mean_type)
        validator.check("batch_std type", batch_std_type,
                        "beta type", beta_type)
        validator.check("batch_std type", batch_std_type,
                        "running_mean type", running_mean_type)
        validator.check("batch_std type", batch_std_type,
                        "gamma type", gamma_type)
        validator.check("x_type", x_type, "batch_std type", batch_std_type)
        validator.check_typename(
            "batch_std type", batch_std_type, (mstype.float16, mstype.float32))
        validator.check_typename(
            "global_step type", global_step_type, (mstype.int32,))
        return x_type


class BatchNormFold2Grad(PrimitiveWithInfer):
    """Performs grad of CorrectionAddGrad operation."""
    channel = 1

    @prim_attr_register
    def __init__(self, freeze_bn=0):
        """init MulFold layer"""
        self.freeze_bn = freeze_bn
        self.init_prim_io_names(inputs=['dout', 'x', 'gamma',
                                        'batch_std', 'batch_mean',
                                        'running_std', 'running_mean', 'global_step'],
                                outputs=['d_batch_std', 'd_batch_mean', 'd_beta', 'd_gamma', 'dx'])

    def infer_shape(self, dout_shape, x_shape, gamma_shape,
                    batch_std_shape, batch_mean_shape,
                    running_std_shape, running_mean_shape, global_step_shape):
        validator.check("batch_std shape", batch_std_shape,
                        "batch_mean shape", batch_mean_shape)
        validator.check("batch_std shape", batch_std_shape,
                        "running_std shape", running_std_shape)
        validator.check("batch_std shape", batch_std_shape,
                        "running_mean shape", running_mean_shape)
        validator.check("batch_std shape", batch_std_shape,
                        "gamma shape", gamma_shape)
        validator.check(
            "batch_std size", batch_std_shape[0], "dout channel size", dout_shape[self.channel])
        validator.check_integer("global_step shape",
                                len(global_step_shape), 1, Rel.EQ)
        return gamma_shape, gamma_shape, gamma_shape, gamma_shape, x_shape

    def infer_dtype(self, dout_type, x_type, gamma_type,
                    batch_std_type, batch_mean_type,
                    running_std_type, running_mean_type, global_step_type):
        validator.check("batch_std type", batch_std_type,
                        "batch_mean type", batch_mean_type)
        validator.check("batch_std type", batch_std_type,
                        "gamma type", gamma_type)
        validator.check("batch_std type", batch_std_type,
                        "running_std type", running_std_type)
        validator.check("batch_std type", batch_std_type,
                        "running_mean type", running_mean_type)
        validator.check("batch_std_type", batch_std_type,
                        "dout type", dout_type)
        validator.check_typename(
            "batch_std type", batch_std_type, (mstype.float16, mstype.float32))
        validator.check_typename(
            "global_step type", global_step_type, (mstype.int32,))
        return gamma_type, gamma_type, gamma_type, gamma_type, gamma_type
