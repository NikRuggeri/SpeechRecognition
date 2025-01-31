from keras.models import Model, load_model

from keras.layers import Input, Activation, Concatenate, Permute, Reshape, Flatten, Lambda, Dot, Softmax
from keras.layers import Add, Dropout, BatchNormalization, Conv2D, Reshape, MaxPooling2D, Dense, CuDNNLSTM, Bidirectional, LSTM, GRU, ConvLSTM2D
from keras import backend as K
from keras.utils import to_categorical
from keras.callbacks import EarlyStopping, ModelCheckpoint, LearningRateScheduler
from keras import backend as K
from keras import optimizers

from kapre.time_frequency import Melspectrogram, Spectrogram
from kapre.utils import Normalization2D

import numpy as np

def ConvSpeechModel(nCategories, samplingrate = 16000, inputLength = 16000):
    """
    Base fully convolutional model for speech recognition
    """

    inputs = Input((inputLength,))

    x = Reshape((1, -1)) (inputs)

    x = Melspectrogram(n_dft=1024, n_hop=128, input_shape=(1, inputLength),
                             padding='same', sr=samplingrate, n_mels=80,
                             fmin=40.0, fmax=samplingrate/2, power_melgram=1.0,
                             return_decibel_melgram=True, trainable_fb=False,
                             trainable_kernel=False,
                             name='mel_stft') (x)
    
    x = Normalization2D(int_axis=0)(x)
    #note that Melspectrogram puts the sequence in shape (batch_size, melDim, timeSteps, 1)
    #we would rather have it the other way around for LSTMs

    x = Permute((2,1,3)) (x)
    #x = Reshape((94,80)) (x) #this is strange - but now we have (batch_size, sequence, vec_dim)

    c1 = Conv2D(20, (5,1) , activation='relu', padding='same') (x)
    c1 = BatchNormalization() (c1)
    p1 = MaxPooling2D((2, 1)) (c1)
    p1 = Dropout(0.03) (p1)

    c2 = Conv2D(40, (3,3) , activation='relu', padding='same') (p1)
    c2 = BatchNormalization() (c2)
    p2 = MaxPooling2D((2, 2)) (c2)
    p2 = Dropout(0.01) (p2)

    c3 = Conv2D(80, (3,3) , activation='relu', padding='same') (p2)
    c3 = BatchNormalization() (c3)
    p3 = MaxPooling2D((2, 2)) (c3)

    p3 = Flatten()(p3)
    p3 = Dense(64, activation = 'relu')(p3)
    p3 = Dense(32, activation = 'relu')(p3)

    output = Dense(nCategories, activation = 'softmax')(p3)

    model = Model(inputs=[inputs], outputs=[output], name='ConvSpeechModel')
    
    return model



def RNNSpeechModel(nCategories, samplingrate = 16000, inputLength = 16000):
    #simple LSTM
    sr = samplingrate
    iLen = inputLength
    
    inputs = Input((iLen,))

    x = Reshape((1, -1)) (inputs)

    x = Melspectrogram(n_dft=1024, n_hop=128, input_shape=(1, iLen),
                             padding='same', sr=sr, n_mels=80,
                             fmin=40.0, fmax=sr/2, power_melgram=1.0,
                             return_decibel_melgram=True, trainable_fb=False,
                             trainable_kernel=False,
                             name='mel_stft') (x)

    x = Normalization2D(int_axis=0)(x)

    #note that Melspectrogram puts the sequence in shape (batch_size, melDim, timeSteps, 1)
    #we would rather have it the other way around for LSTMs

    x = Permute((2,1,3)) (x)

    x = Conv2D(10, (5,1) , activation='relu', padding='same') (x)
    x = BatchNormalization() (x)
    x = Conv2D(1, (5,1) , activation='relu', padding='same') (x)
    x = BatchNormalization() (x)

    #x = Reshape((125, 80)) (x)
    x = Lambda(lambda q: K.squeeze(q, -1), name='squeeze_last_dim') (x) #keras.backend.squeeze(x, axis)

    # CHANGE IF USING GPU
    #x = Bidirectional(CuDNNLSTM(64, return_sequences = True)) (x) # [b_s, seq_len, vec_dim]
    #x = Bidirectional(CuDNNLSTM(64)) (x)
    x = Bidirectional(LSTM(64, return_sequences = True)) (x) # [b_s, seq_len, vec_dim]
    x = Bidirectional(LSTM(64)) (x)

    x = Dense(64, activation = 'relu')(x)
    x = Dense(32, activation = 'relu')(x)

    output = Dense(nCategories, activation = 'softmax')(x)

    model = Model(inputs=[inputs], outputs=[output])
    
    return model


def AttRNNSpeechModel(nCategories, samplingrate = 16000, inputLength = 16000):
    #simple LSTM
    sr = samplingrate
    iLen = inputLength
    
    inputs = Input((sr,))

    x = Reshape((1, -1)) (inputs)

    x = Melspectrogram(n_dft=1024, n_hop=128, input_shape=(1, iLen),
                             padding='same', sr=sr, n_mels=80,
                             fmin=40.0, fmax=sr/2, power_melgram=1.0,
                             return_decibel_melgram=True, trainable_fb=False,
                             trainable_kernel=False,
                             name='mel_stft') (x)

    x = Normalization2D(int_axis=0)(x)

    #note that Melspectrogram puts the sequence in shape (batch_size, melDim, timeSteps, 1)
    #we would rather have it the other way around for LSTMs

    x = Permute((2,1,3)) (x)

    x = Conv2D(10, (5,1) , activation='relu', padding='same') (x)
    x = BatchNormalization()(x)
    x = Conv2D(10, (5,1) , activation='relu', padding='same') (x)
    x = BatchNormalization()(x)
    x = Conv2D(10, (5,1) , activation='relu', padding='same') (x)
    x = BatchNormalization()(x)
    x = Conv2D(1, (5,1) , activation='relu', padding='same') (x)
    x = BatchNormalization()(x)

    #x = Reshape((125, 80)) (x)
    x = Lambda(lambda q: K.squeeze(q, -1), name='squeeze_last_dim') (x) #keras.backend.squeeze(x, axis)

    # CHANGE IF USING GPU
    #x = Bidirectional(CuDNNLSTM(64, return_sequences = True)) (x) # [b_s, seq_len, vec_dim]
    #x = Bidirectional(CuDNNLSTM(64, return_sequences = True)) (x) # [b_s, seq_len, vec_dim]
    x = Bidirectional(LSTM(64, return_sequences = True)) (x) # [b_s, seq_len, vec_dim]
    x = Bidirectional(LSTM(64, return_sequences = True)) (x) # [b_s, seq_len, vec_dim]
    x = Bidirectional(LSTM(64, return_sequences = True)) (x) # [b_s, seq_len, vec_dim]


    xFirst = Lambda(lambda q: q[:,64]) (x) #[b_s, vec_dim]
    query = Dense(128) (xFirst)

    #dot product attention
    attScores = Dot(axes=[1,2])([query, x]) 
    attScores = Softmax(name='attSoftmax')(attScores) #[b_s, seq_len]

    #rescale sequence
    attVector = Dot(axes=[1,1])([attScores, x]) #[b_s, vec_dim]

    x = Dense(64, activation = 'relu')(attVector)
    x = Dense(32)(x)

    output = Dense(nCategories, activation = 'softmax', name='output')(x)

    model = Model(inputs=[inputs], outputs=[output])
    
    return model



##################################################################
# ------- START OF OUR MODIFICATIONS OF THE MODELS ------------- # 
##################################################################

# Use GRU instead of LSTM
def AttGRUSpeechModel(nCategories, samplingrate = 16000, inputLength = 16000):
    #simple LSTM
    sr = samplingrate
    iLen = inputLength
    
    inputs = Input((sr,))

    x = Reshape((1, -1)) (inputs)

    x = Melspectrogram(n_dft=1024, n_hop=128, input_shape=(1, iLen),
                             padding='same', sr=sr, n_mels=80,
                             fmin=40.0, fmax=sr/2, power_melgram=1.0,
                             return_decibel_melgram=True, trainable_fb=False,
                             trainable_kernel=False,
                             name='mel_stft') (x)

    x = Normalization2D(int_axis=0)(x)

    #note that Melspectrogram puts the sequence in shape (batch_size, melDim, timeSteps, 1)
    #we would rather have it the other way around for LSTMs

    x = Permute((2,1,3)) (x)

    x = Conv2D(10, (5,1) , activation='relu', padding='same') (x)
    x = BatchNormalization() (x)
    x = Conv2D(1, (5,1) , activation='relu', padding='same') (x)
    x = BatchNormalization() (x)

    #x = Reshape((125, 80)) (x)
    x = Lambda(lambda q: K.squeeze(q, -1), name='squeeze_last_dim') (x) #keras.backend.squeeze(x, axis)

    x = Bidirectional(GRU(64, return_sequences = True)) (x) # [b_s, seq_len, vec_dim]
    x = Bidirectional(GRU(64, return_sequences = True)) (x) # [b_s, seq_len, vec_dim]


    xFirst = Lambda(lambda q: q[:,64]) (x) #[b_s, vec_dim]
    query = Dense(128) (xFirst)

    #dot product attention
    attScores = Dot(axes=[1,2])([query, x]) 
    attScores = Softmax(name='attSoftmax')(attScores) #[b_s, seq_len]

    #rescale sequence
    attVector = Dot(axes=[1,1])([attScores, x]) #[b_s, vec_dim]

    x = Dense(64, activation = 'relu')(attVector)
    x = Dense(32)(x)

    output = Dense(nCategories, activation = 'softmax', name='output')(x)

    model = Model(inputs=[inputs], outputs=[output])
    
    return model



# Use convolutional LSTM 
def AttConvLSTMSpeechModel(nCategories, samplingrate = 16000, inputLength = 16000, dropout = 0):
    #simple LSTM
    sr = samplingrate
    iLen = inputLength
    
    inputs = Input((sr,))

    x = Reshape((1, -1)) (inputs)

    x = Melspectrogram(n_dft=1024, n_hop=128, input_shape=(1, iLen),
                             padding='same', sr=sr, n_mels=80,
                             fmin=40.0, fmax=sr/2, power_melgram=1.0,
                             return_decibel_melgram=True, trainable_fb=False,
                             trainable_kernel=False,
                             name='mel_stft') (x)

    x = Normalization2D(int_axis=0)(x)

    #note that Melspectrogram puts the sequence in shape (batch_size, melDim, timeSteps, 1)
    #we would rather have it the other way around for LSTMs

    x = Permute((2,1,3)) (x)

    x = Conv2D(10, (5,1) , activation='relu', padding='same') (x)
    x = BatchNormalization() (x)
    x = Conv2D(1, (5,1) , activation='relu', padding='same') (x)
    x = BatchNormalization() (x)

    # x = Reshape((125, 80)) (x)
    x = Lambda(lambda q: K.squeeze(q, -1), name='squeeze_last_dim') (x) #keras.backend.squeeze(x, axis)

    # add axis to comply with shape requirements for ConvLSTM2D
    x = Lambda(lambda q: q[:, np.newaxis,  np.newaxis, :, :])(x)

    # note that convoltions modify the shape of the tensors, we would need to adapt the consequent part of the network
    x = Bidirectional(ConvLSTM2D(filters=1, data_format='channels_first', kernel_size= (5,1), return_sequences = True, padding='same', dropout = dropout)) (x) # [b_s, 1, 1, seq_len, vec_dim]
    x = Bidirectional(ConvLSTM2D(filters=1, data_format='channels_first', kernel_size= (5,1), return_sequences = True, padding='same')) (x) # [b_s, 1, 1, seq_len, vec_dim]

    # we still conider the middle vector, but we have a different shape due to the ConvLSTM layer
    # first remove the extra dimensions
    x = Lambda(lambda q: K.squeeze(q, axis= 2))(x) 
    x = Lambda(lambda q: K.squeeze(q, axis= 1))(x)  # [b_s, seq_len, vec_dim]
    # NIK: we want to preserve interpretability of the attention. To do so we take shape back to the initial one
    x = Dense(128)(x)
    xFirst = Lambda(lambda q: q[:,61]) (x) #[b_s, vec_dim]
    query = Dense(128) (xFirst)

    #dot product attention
    attScores = Dot(axes=[1,2])([query, x]) 
    attScores = Softmax(name='attSoftmax')(attScores) #[b_s, seq_len]

    #rescale sequence
    attVector = Dot(axes=[1,1])([attScores, x]) #[b_s, vec_dim]

    x = Dense(64, activation = 'relu')(attVector)
    x = Dense(32)(x)

    output = Dense(nCategories, activation = 'softmax', name='output')(x)

    model = Model(inputs=[inputs], outputs=[output])
    
    return model


# feed attention mechanism with average of features instead of middle one
def AttRNNSpeechModel(nCategories, samplingrate = 16000, inputLength = 16000):
    #simple LSTM
    sr = samplingrate
    iLen = inputLength
    
    inputs = Input((sr,))

    x = Reshape((1, -1)) (inputs)

    x = Melspectrogram(n_dft=1024, n_hop=128, input_shape=(1, iLen),
                             padding='same', sr=sr, n_mels=80,
                             fmin=40.0, fmax=sr/2, power_melgram=1.0,
                             return_decibel_melgram=True, trainable_fb=False,
                             trainable_kernel=False,
                             name='mel_stft') (x)

    x = Normalization2D(int_axis=0)(x)

    #note that Melspectrogram puts the sequence in shape (batch_size, melDim, timeSteps, 1)
    #we would rather have it the other way around for LSTMs

    x = Permute((2,1,3)) (x)

    x = Conv2D(10, (5,1) , activation='relu', padding='same') (x)
    x = BatchNormalization()(x)
    x = Conv2D(10, (5,1) , activation='relu', padding='same') (x)
    x = BatchNormalization()(x)
    x = Conv2D(10, (5,1) , activation='relu', padding='same') (x)
    x = BatchNormalization()(x)
    x = Conv2D(1, (5,1) , activation='relu', padding='same') (x)
    x = BatchNormalization()(x)

    #x = Reshape((125, 80)) (x)
    x = Lambda(lambda q: K.squeeze(q, -1), name='squeeze_last_dim') (x) #keras.backend.squeeze(x, axis)

    # CHANGE IF USING GPU
    #x = Bidirectional(CuDNNLSTM(64, return_sequences = True)) (x) # [b_s, seq_len, vec_dim]
    #x = Bidirectional(CuDNNLSTM(64, return_sequences = True)) (x) # [b_s, seq_len, vec_dim]
    x = Bidirectional(LSTM(64, return_sequences = True)) (x) # [b_s, seq_len, vec_dim]
    x = Bidirectional(LSTM(64, return_sequences = True)) (x) # [b_s, seq_len, vec_dim]


    xFirst = Lambda(lambda q: K.mean( x, axis=1, keepdims=False)) (x) #[b_s, vec_dim]
    query = Dense(128) (xFirst)

    #dot product attention
    attScores = Dot(axes=[1,2])([query, x]) 
    attScores = Softmax(name='attSoftmax')(attScores) #[b_s, seq_len]

    #rescale sequence
    attVector = Dot(axes=[1,1])([attScores, x]) #[b_s, vec_dim]

    x = Dense(64, activation = 'relu')(attVector)
    x = Dense(32)(x)

    output = Dense(nCategories, activation = 'softmax', name='output')(x)

    model = Model(inputs=[inputs], outputs=[output])
    
    return model


# compress convolution and attention into a ConvLSTM
def CompressedAttLSTMpeechModel(nCategories, samplingrate = 16000, inputLength = 16000):
    #simple LSTM
    sr = samplingrate
    iLen = inputLength
    
    inputs = Input((sr,))

    x = Reshape((1, -1)) (inputs)

    x = Melspectrogram(n_dft=1024, n_hop=128, input_shape=(1, iLen),
                             padding='same', sr=sr, n_mels=80,
                             fmin=40.0, fmax=sr/2, power_melgram=1.0,
                             return_decibel_melgram=True, trainable_fb=False,
                             trainable_kernel=False,
                             name='mel_stft') (x)

    x = Normalization2D(int_axis=0)(x)

    #note that Melspectrogram puts the sequence in shape (batch_size, melDim, timeSteps, 1)
    #we would rather have it the other way around for LSTMs
    x = Permute((2,1,3)) (x)
    x = Lambda(lambda q: K.squeeze(q, axis = -1)) (x) # [b_s, timeSteps, melDim]
    # add axis to comply with shape requirements for ConvLSTM2D
    x = Lambda(lambda q: q[:, np.newaxis, np.newaxis, :, :])(x) # [b_s, timeSteps, melDim, 1, 1]

    x = Bidirectional(ConvLSTM2D(filters=10, data_format='channels_first', kernel_size= (5,1), activation='relu', return_sequences = False, padding='same')) (x) # [b_s, 1, 1, seq_len, vec_dim]
    x = BatchNormalization() (x)
    x = Lambda(lambda q: q[:, np.newaxis, :, :, :])(x)
    x = Bidirectional(ConvLSTM2D(filters=5, data_format='channels_first', kernel_size= (5,1), activation='relu', return_sequences = False, padding='same')) (x) # [b_s, 1, 1, seq_len, vec_dim]
    x = BatchNormalization() (x)
    x = Lambda(lambda q: q[:, np.newaxis, :, :, :])(x)
    x = Bidirectional(ConvLSTM2D(filters=1, data_format='channels_first', kernel_size= (5,1), activation='relu', return_sequences = False, padding='same')) (x) # [b_s, 1, 1, seq_len, vec_dim]
    x = BatchNormalization() (x)
    
    #x = Reshape((125, 80)) (x)
    x = Lambda(lambda q: K.squeeze(q, axis=1), name='squeeze_dims') (x) #keras.backend.squeeze(x, axis)
    # reduce to dimension 128 like in paper's model
    x = Dense(128)(x)

    xFirst = Lambda(lambda q: q[:,61]) (x) #[b_s, vec_dim]
    query = Dense(128) (xFirst)

    #dot product attention
    attScores = Dot(axes=[1,2])([query, x]) 
    attScores = Softmax(name='attSoftmax')(attScores) #[b_s, seq_len]

    #rescale sequence
    attVector = Dot(axes=[1,1])([attScores, x]) #[b_s, vec_dim]

    x = Dense(64, activation = 'relu')(attVector)
    x = Dense(32)(x)

    output = Dense(nCategories, activation = 'softmax', name='output')(x)

    model = Model(inputs=[inputs], outputs=[output])
    
    return model
