import io
import os.path
from matplotlib import pyplot as plt
import tensorflow as tf
import tensorflow_io as tfio

#Tensorflow Dependencies
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, Dense, Flatten


CAPUCHIN_FILE= os.path.join('C:', os.sep,'Users','kevin','Downloads','archive','Parsed_Capuchinbird_Clips','XC3776-3.wav')
NOT_CAPUCHIN_FILE= os.path.join('C:', os.sep,'Users','kevin','Downloads','archive','Parsed_Not_Capuchinbird_Clips','afternoon-birds-song-in-forest-0.wav')

#BUILD DATALOADING FUNCTION
def load_wav_16k_mono(filename):
    # Load encoded wav file
    file_contents = tf.io.read_file(filename)
    # Decode wav (tensors by channels)
    wav, sample_rate = tf.audio.decode_wav(file_contents, desired_channels=1)
    # Removes trailing axis
    wav = tf.squeeze(wav, axis=-1)
    sample_rate = tf.cast(sample_rate, dtype=tf.int64)
    # Goes from 44100Hz to 16000hz - amplitude of the audio signal
    wav = tfio.audio.resample(wav, rate_in=sample_rate, rate_out=16000)
    return wav


#PLOT WAVE
wave=load_wav_16k_mono(CAPUCHIN_FILE)
nwave=load_wav_16k_mono(NOT_CAPUCHIN_FILE)
plt.plot(wave)
plt.plot(nwave)
plt.show()

#CREATE TENSORFLOW DATASET
#define paths to positive and negative data
POS= os.path.join('C:', os.sep,'Users','kevin','Downloads','archive','Parsed_Capuchinbird_Clips')
NEG= os.path.join('C:', os.sep,'Users','kevin','Downloads','archive','Parsed_Not_Capuchinbird_Clips')

#Create Tensorflow Datasets
pos= tf.data.Dataset.list_files(POS+'\*.wav')
neg= tf.data.Dataset.list_files(NEG+'\*.wav')

#Add Lables and combine positive and negative samples ,Flag 1 if COMBU Flag 0 if not COMB
positives = tf.data.Dataset.zip((pos,tf.data.Dataset.from_tensor_slices(tf.ones(len(pos)))))
negatives = tf.data.Dataset.zip((neg,tf.data.Dataset.from_tensor_slices(tf.zeros(len(pos)))))
data = positives.concatenate(negatives)

#DETERMINE AVERAGE LENGTH OF A CAPUCHIN CALL
#Calculate wave cycle length
lengths = []
for file in os.listdir(os.path.join('C:', os.sep,'Users','kevin','Downloads','archive','Parsed_Capuchinbird_Clips')):
    tensor_wave = load_wav_16k_mono(os.path.join('C:', os.sep,'Users','kevin','Downloads','archive','Parsed_Capuchinbird_Clips', file))
    lengths.append(len(tensor_wave))

os.listdir(os.path.join('C:', os.sep,'Users','kevin','Downloads','archive','Parsed_Capuchinbird_Clips'))

#BUILD PROCESSING FUNCTION
#Build preprocessing function

def preprocess(file_path,lable):
    wav=load_wav_16k_mono(file_path)
    wav= wav[:48000]
    zero_padding = tf.zeros([48000]-tf.shape(wav),dtype=tf.float32)
    wav=tf.concat([zero_padding,wav],0)
    spectrogram=tf.signal.stft(wav,frame_length=320,frame_step=32)
    spectrogram=tf.abs(spectrogram)
    spectrogram=tf.expand_dims(spectrogram,axis=2)
    return spectrogram, lable

#Test out the functions and viz the spectrogram
filepath,lable=positives.shuffle(buffer_size=10000).as_numpy_iterator().next()
spectrogram,lable=preprocess(filepath,lable)
plt.figure(figsize=(30,20))
plt.imshow(tf.transpose(spectrogram)[0])
plt.show()

#CREATING AND TESTING PARTITIONS
#Create a Tensorflow Data Pipeline
data = data.map(preprocess)
data = data.cache()
data = data.shuffle(buffer_size=1000)
data = data.batch(16)
data = data.prefetch(8)

#Split into training and testing partitions
len(data)*.7
train = data.take(36)
test = data.skip(36).take(15)

#Test one batch
sample, lables = train.as_numpy_iterator().next()
sample.shape #SPECTROGRAM SHAPE = 1491, 257,1

#Build Sequential Model, Complie and view summary
model = Sequential()
model.add(Conv2D(16,(3,3), activation='relu', input_shape=(1491, 257,1)))
model.add(Conv2D(16,(3,3), activation='relu'))
model.add(Flatten())
model.add(Dense(128, activation='relu'))
model.add(Dense(1, activation='sigmoid'))

model.compile('Adam', loss='BinaryCrossentropy', metrics=[tf.keras.metrics.Recall(), tf.keras.metrics.Precision()] )
print(model.summary())

#Fit Model, View Loss, KPI Plots
hist = model.fit(train, epochs= 4, validation_data= test)

plt.title('Loss')
plt.plot(hist.history['loss'],'r')
plt.plot(hist.history['val_loss'],'b')
plt.show()
