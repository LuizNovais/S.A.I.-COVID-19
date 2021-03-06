from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model
from imutils.video import VideoStream
import numpy as np
import argparse
import imutils
import time
import cv2
import os
import serial
import time
import threading
import statistics



def detect_and_predict_mask(frame, faceNet, maskNet):

    (h, w) = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300),
                                 (104.0, 177.0, 123.0))

    faceNet.setInput(blob)
    detections = faceNet.forward()

    faces = []
    locs = []
    preds = []

    for i in range(0, detections.shape[2]):
        confidence = detections[0, 0, i, 2]

        if confidence > args["confidence"]:
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")

            (startX, startY) = (max(0, startX), max(0, startY))
            (endX, endY) = (min(w - 1, endX), min(h - 1, endY))

            face = frame[startY:endY, startX:endX]
            face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
            face = cv2.resize(face, (224, 224))
            face = img_to_array(face)
            face = preprocess_input(face)

            faces.append(face)
            locs.append((startX, startY, endX, endY))


    if len(faces) > 0:
        faces = np.array(faces, dtype="float32")
        preds = maskNet.predict(faces, batch_size=32)

    return (locs, preds)


def getinfo():  # Função que abre comunicação serial com o microcontrolador e recebe as medições
    global flag_info
    global sensor
    c = 0  # Variável iterativa
    str_data = ''  # String que recebe as medições uma a uma na leitura da porta serial
    temp_l = []  # Lista que recebe as 10 medições de temperatura.
    oxi_l = []  # Lista que recebe as 10 medições de oxigenação.
    flag_info = 1
    arduino = serial.Serial('COM3', 115200, timeout=.1)  # Variável que inicia a comunicação serial com o microcontrolador, como parâmetros:
    # 'COM3': Porta USB que o microcontrolador está conectado; 115200: Baud Rate
    while str_data != 't':  # Loop que envia o caracter t ao microcontrolador solicitando as medições de temperatura
        arduino.write(bytes('t', 'utf-8'))  # Escreve o caractere t na porta serial
        time.sleep(0.5)  # Aguarda 0,5 segundos
        data = arduino.readline()  # Lê o conteúdo da porta serial e aloca na variável data
        str_data = data.rstrip().decode('utf-8')  # Decodifica o dado hexadecimal e aloca na variável str_data
        time.sleep(0.5)  # O programa fica repetindo o envio de t, até receber do microcontrolador um t como confirmação de que está pronto para o envio das medições
    while str_data != 'f':  # Loop para leitura e arquivo das medições, até que receba o caractere f que sinaliza o fim do envio de medições
        data = arduino.readline()  # Lê o conteúdo da porta serial e aloca na variável data
        str_data = data.rstrip().decode('utf-8')  # Decodifica o dado hexadecimal e aloca na variável str_data
        if str_data != 'f': temp_l.append(str_data)  # Guarda o valor recebido em strdata como um novo item na lista temp_l
        time.sleep(0.1)  # Aguarda 0,1 segundos
    time.sleep(0.5)  # Aguarda 0,5 segundos
    while str_data != 'o':  # Loop que envia o caracter o ao microcontrolador solicitando as medições de oxigenação
        arduino.write(bytes('o', 'utf-8'))  # Escreve o caractere o na porta serial
        time.sleep(0.5)  # Aguarda 0,5 segundos
        data = arduino.readline()  # Lê o conteúdo da porta serial e aloca na variável data
        str_data = data.rstrip().decode('utf-8')  # Decodifica o dado hexadecimal e aloca na variável str_data
        time.sleep(0.5)  # O programa fica repetindo o envio de o, até receber do microcontrolador um o como confirmação de que está pronto para o envio das medições
    while (str_data != 'f'):  # Loop para leitura e arquivo das medições, até que receba o caractere f que sinaliza o fim do envio de medições
        data = arduino.readline()  # Lê o conteúdo da porta serial e aloca na variável data
        str_data = data.rstrip().decode('utf-8')  # Decodifica o dado hexadecimal e aloca na variável str_data
        if str_data != 'f': oxi_l.append(str_data)  # Guarda o valor recebido em strdata como um novo item na lista temp_l
        time.sleep(1)  # Aguarda 1 segundos, o oximetro necessita de um tempo maior para atualizar as medições
    arduino.close()  # Encerra a comunicação serial com o microcontrolador
    flag_info = 0
    sensor = 0

    return (temp_l, oxi_l)  # Retorna as duas listas como resultado da função


def measures():  # Função que trata as medições recebidas e prepara para exibição
    global ox1  # Variável que recebe o valor de oxigenação a ser exibido
    global ox2  # Lista de medições confiáveis de oxigenação
    global temp1  # Variável que recebe o valor de temperatura a ser exibido
    global temp2  # Lista de medições confiáveis de oxigenação
    global sensor #Variável global que guarda a informação do sensor de presença
    global flag_info #Variável global que fica em nível lógico alto quando a comunicação com o microcontrolador é iniciada.
    oxix = []  # Variável local que recebe a lista de medições de oxigenação
    tempx = []  # Variável local que recebe a lista de medições de temperatura
    double_list = getinfo()  # Chama a função getinfo() e aloca as duas listas com as medições na variáve double_list
    oxix.append(double_list[1])  # Aloca a lista de medições de oxigenação na oxix
    ox = oxix[0]  # Formatação da lista
    for i in ox:
        if float(i) > 10 and float(i) < 101:  # Iteração para transformar os valores texto em numéricos e para ignorar valores abaixo de 10% e acima de 101%
            ox2.append(i)
    if len(ox2) > 0:
        ox1 = str(statistics.mode(ox2))  # Dos valores que estão na faixa selecionada, realiza a moda e aloca na variável ox1
    else:
        ox1 = 'Leitura não realizada corretamente'  # Dos valores que estão na faixa selecionada, realiza a moda e aloca na variável ox1
    tempx.append(double_list[0])  # Aloca a lista de medições de temperatura na tempx
    temp = tempx[0]  # Formatação da lista
    for i in temp:
        if float(i) > 10 and float(
                i) < 101:  # Iteração para transformar os valores texto em numéricos e para ignorar valores abaixo de 10% e acima de 101%
            temp2.append(i)
    temp1 = str(
        statistics.mode(temp2))  # Dos valores que estão na faixa selecionada, realiza a moda e aloca na variável ox1


def pix():
    global sensor
    global flag_info
    str_data = ''
    #while True:
    while flag_info == 0:  # Loop que envia o caracter t ao microcontrolador solicitando as medições de temperatura
        time.sleep(1)
        arduino = serial.Serial('COM3', 115200, timeout=.1)
        str_data = ''
        while str_data != 'f' and str_data != 'p':
            arduino.write(bytes('p', 'utf-8'))  # Escreve o caractere p na porta serial
            time.sleep(0.5)  # Aguarda 0,1 segundos
            data = arduino.readline()  # Lê o conteúdo da porta serial e aloca na variável data
            str_data = data.rstrip().decode('utf-8')  # Decodifica o dado hexadecimal e aloca na variável str_data
            if str_data == 'p':
                sensor = 1
                arduino.close()  # Encerra a comunicação serial com o microcontrolador
            elif str_data == 'f':
                sensor = 0
                arduino.close()  # Encerra a comunicação serial com o microcontrolador
            time.sleep(5)  # O programa fica repetindo o envio de t, até receber do microcontrolador um t como confirmação de que está pronto para o envio das medições
    #time.sleep(0.5)


# Inicialização das variáveis de controle e construção dos argumentos
ox1 = "0"
ox2 = []
temp1 = "0"
temp2 = []
old_ox1 = "0"
old_temp1 = "0"
old_label = ""
sensor = 0
flag_info = 0
flag_pix = 0
ap = argparse.ArgumentParser()
ap.add_argument("-f", "--face", type=str,
                default="face_detector",
                help="path to face detector model directory")
ap.add_argument("-m", "--model", type=str,
                default="mask_detector.model",
                help="path to trained face mask detector model")
ap.add_argument("-c", "--confidence", type=float, default=0.5,
                help="minimum probability to filter weak detections")
args = vars(ap.parse_args())

print("[INFO] Carregando detector de máscara...")
prototxtPath = os.path.sep.join([args["face"], "deploy.prototxt"])
weightsPath = os.path.sep.join([args["face"],
                                "res10_300x300_ssd_iter_140000.caffemodel"])
faceNet = cv2.dnn.readNet(prototxtPath, weightsPath)

maskNet = load_model(args["model"])

print("[INFO] starting video stream...")
vs = VideoStream(src=0).start()
time.sleep(2.0)

while True:
    frame = vs.read()
    frame = imutils.resize(frame, width=800)

    (locs, preds) = detect_and_predict_mask(frame, faceNet, maskNet)

    for (box, pred) in zip(locs, preds):
        (startX, startY, endX, endY) = box
        (mask, withoutMask) = pred

        if mask > 0.5 and flag_info == 0 and flag_pix == 0:
            threading.Thread(target=pix).start()
            flag_pix = 1
        elif mask < 0.5:
            flag_pix = 0
        if mask > withoutMask:
            label = "Com Mascara"
        else:
            label = "Sem Mascara"  # Classifica se o rosto identificado está de mascara
        color = (0, 255, 0) if label == "Com Mascara" else (0, 0, 255)  # Altera a cor da frase
        if label == "Sem Mascara":
            label6 = ("Por favor, coloque a mascara")  # Se o usuário estiver sem máscara, solicita que coloque
            color6 = (0, 255, 255)
            org6 = (260, 225)
            cv2.putText(frame, label6, org6, cv2.FONT_HERSHEY_SIMPLEX, 0.55, color6, 2)

        if sensor == 1 and flag_info == 0:  # Se há uma alteração no estado de Sem Máscara para Com Máscara
            threading.Thread(target=measures).start()  # Executa a função que solicita as medidas
        if ox1 != old_ox1:  # Quando as novas medidas são atualizadas
            label1 = (f"Oxigenacao = {ox1}")  # É informado na tela o valor de oxigenação
            org1 = (500, 515)
            label2 = (f"Temperatura = {temp1}")  # Temperatura
            org2 = (500, 545)
            label4 = ("Entrada autorizada")  # Entrada autorizada
            org4 = (260, 225)
            label5 = ("Entrada nao autorizada")  # Ou não autorizada
            org5 = (260, 225)
            cv2.putText(frame, label1, org1, cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
            cv2.putText(frame, label2, org2, cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

            if label == "Com Mascara" and float(temp1) < 36.2 and float(ox1) >= 94.0:  # Se o usuário está de máscara, possui temperatura e oxigenação dentro da faixa aceitável
                cv2.putText(frame, label4, org4, cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)  # Exibe entrada autorizada
            else:
                cv2.putText(frame, label5, org5, cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)  # Se não, exibe entrada não autorizada
            key = cv2.waitKey(1) & 0xFF
            c = + 1
            if c > 10 or label != old_label:
                old_ox1 = ox1
        else:  # Enquanto as medidas não são atualizadas
            label3 = ("Coloque o dedo no local indicado")  # Solicita que o usuário posicione o dedo
            org3 = (500, 485)
            cv2.putText(frame, label3, org3,
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 2)
            key = cv2.waitKey(1) & 0xFF
        old_label = label

    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

cv2.destroyAllWindows()
vs.stop()