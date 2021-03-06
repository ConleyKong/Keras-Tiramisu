from keras.layers import Activation
from keras.layers import Lambda
from keras.layers import Conv2D
from keras.layers import Conv2DTranspose
from keras.layers import AlphaDropout
from keras.layers import MaxPooling2D
from keras.layers import concatenate
from keras.layers import Input
from keras.models import Model
from keras import regularizers

def layer(k, x):
    x = Activation('selu')(x)
    x = Conv2D(k, 3, padding='same', kernel_initializer='lecun_normal', kernel_regularizer=regularizers.l2(1e-4))(x)
    return AlphaDropout(0.2)(x)

def transitionDown(filters, x):
    x = Activation('selu')(x)
    x = Conv2D(filters, 1, padding='same', kernel_initializer='lecun_normal', kernel_regularizer=regularizers.l2(1e-4))(x)
    x = AlphaDropout(0.2)(x)
    return MaxPooling2D(pool_size=2)(x)

def transitionUp(filters, x):
    return Conv2DTranspose(filters, 3, padding='same', strides=(2,2), kernel_initializer='lecun_normal', kernel_regularizer=regularizers.l2(1e-4))(x)

def denseBlock(k, n, x):
    for i in range(n):
        x = concatenate([x, layer(k,x)])
    return x

def build(width, height, n_classes, weights_path=None):
    input = Input(shape=(height, width, 3))
    
    x = Lambda(lambda x: (x - 114.535627228)/68.4730185592)(input) # Normalize to 0 mean and 1 stddev
    x = Conv2D(48, 3, padding='same', kernel_initializer='lecun_normal', kernel_regularizer=regularizers.l2(1e-4))(x)

    # DOWN
    skip1 = denseBlock(16, 4, x)
    x = transitionDown(112, skip1)

    skip2 = denseBlock(16, 5, x)
    x = transitionDown(192, skip2)

    skip3 = denseBlock(16, 7, x)
    x = transitionDown(304, skip3)

    skip4 = denseBlock(16, 10, x)
    x = transitionDown(464, skip4)

    skip5 = denseBlock(16, 12, x)
    x = transitionDown(656, skip5)

    # BOTTLENECK
    x = denseBlock(16, 15, x)

    # UP
    x = concatenate([transitionUp(240, x), skip5])
    x = denseBlock(16, 12, x)

    x = concatenate([transitionUp(192, x), skip4])
    x = denseBlock(16, 10, x)

    x = concatenate([transitionUp(160, x), skip3])
    x = denseBlock(16, 7, x)

    x = concatenate([transitionUp(112, x), skip2])
    x = denseBlock(16, 5, x)

    x = concatenate([transitionUp(80, x), skip1])
    x = denseBlock(16, 4, x)

    # OUTPUT
    output = Conv2D(n_classes, 1, activation='softmax', kernel_initializer='lecun_normal', kernel_regularizer=regularizers.l2(1e-4))(x)

    model = Model(inputs=input, outputs=output)
    if weights_path is not None:
        model.load_weights(weights_path)
    return model
