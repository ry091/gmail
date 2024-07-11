import json
import re
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import os


def uso_selenium(email, passw):
    chrome_options = Options()
    chrome_options.add_argument("user-data-dir=selenium_profile")  # Guarda los datos del perfil en la carpeta 'selenium_profile'
    chrome_options.add_argument("--start-maximized")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get("")


    driver.refresh()  
    try:
        if WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".css-6y7f4j"))):
            google = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".css-6y7f4j")))
            google.click()
            username = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='email']")))
            username.send_keys(email)
            username.send_keys(Keys.ENTER)
            password = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='password']")))
            password.send_keys(passw)
            password.send_keys(Keys.ENTER)

            print("Login successful and cookies saved")
    except:
        pass

    return driver

def web_911(driver, datos_correo):
    name_equipo = "requested_item_values_111_requested_item_value_attributes_cf_cantidad_de_equipos_afectados_197851"
    cantidad_equipos = WebDriverWait(driver, 40).until(EC.visibility_of_element_located((By.ID, name_equipo)))
    cantidad_equipos.send_keys(str(len(datos_correo['ip'])))
    
    element = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.ID, "requested_item_values_111_requested_item_value_attributes_cf_tipo_de_evento_197851")))
    select_element = Select(element)
    select_element.select_by_visible_text("Alerta en Perimetrales")

    filial = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.ID, "requested_item_values_111_requested_item_value_attributes_cf_filial_197851")))
    select_filial = Select(filial)
    if "CMD" in datos_correo.get("sucursal", ""):
        select_filial.select_by_visible_text("CMD")
        sucursal = WebDriverWait(driver, 25).until(EC.visibility_of_element_located((By.ID, "requested_item_values_111_requested_item_value_attributes_cf_01_sucursal_197851")))
        select_sucursal = Select(sucursal)
        select_sucursal.select_by_visible_text("Todo CMD")
    else:
        select_filial.select_by_visible_text("Clínica")
        sucursal = WebDriverWait(driver, 25).until(EC.visibility_of_element_located((By.ID, "requested_item_values_111_requested_item_value_attributes_cf_01_sucursal_197851")))
        ubicacion = f"Clínica {datos_correo['sucursal'][0]}"
        select_sucursal = Select(sucursal)
        select_sucursal.select_by_visible_text(ubicacion)

    descripcion = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.ID, "requested_item_values_111_requested_item_value_attributes_cf_descripcion_del_evento_de_seguridad_197851")))
    descripcion.send_keys(datos_correo['asunto'])
    #boton "colocar solicitud"
    #ubmit_button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit'][value='Colocar solicitud']")))
    #submit_button.click()
    input("ENTER para continuar")
    
    
def authenticate():
    SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    creds = flow.run_local_server(port=0)
    service = build("gmail", "v1", credentials=creds)
    return service

def etiqueta(service):
    label_ver = service.users().labels().list(userId="me").execute().get("labels", [])
    nombre_etiqueta = "Revision IP"
    for label in label_ver:
        if label["name"] == nombre_etiqueta:
            return label["id"]
    body = {
        "name": nombre_etiqueta,
        "messageListVisibility": "show",
        "labelListVisibility": "labelShow"
    }
    etiqueta = service.users().labels().create(userId="me", body=body).execute()
    return etiqueta["id"]

def filter_messages(service, etiqueta):
    query = "Revision IP is:unread -label:Revision IP -subject:re "
    results = service.users().messages().list(userId="me", q=query).execute()
    messages = results.get("messages", [])
    data = []
    if not messages:
        print("No hay mensajes. \n")
    else:
        for message in messages:
            msg = service.users().messages().get(userId="me", id=message["id"]).execute()
            mensaje = "Favor efectuar las siguientes acciones / validaciones:\nEl antivirus se encuentre instalado y con sus patrones de firma al día.\nEjecutar un escaneo con la herramienta de antivirus en dispositivo he indicar resultados.\nDeterminar si es necesario borrar archivos temporales descargados o almacenados en el equipo"
            asunto = ""
            for header in msg["payload"]["headers"]:
                if header["name"] == "Subject":
                    asunto = header["value"]
                    break
            ip = re.findall(r'\d+\.\d+\.\d+\.\d+', asunto)
            fw_location = re.findall(r'FW\s+(\w+)', asunto)
            info = {
                "asunto": f"{asunto}: \n{mensaje}",
                "ip": ip,
                "sucursal": fw_location
            }
            data.append(info)
            service.users().messages().modify(userId="me", id=message["id"], body={"removeLabelIds": ["UNREAD"], "addLabelIds": [etiqueta]}).execute()
    return data

def main():
    email = "correo@"
    passw = "contraseña"
    
    service = authenticate()
    label = etiqueta(service)
    user_data = filter_messages(service, label)
    print("total correos: ", len(user_data))

    for i in user_data:
        driver = uso_selenium(email, passw)
        web_911(driver, i)

if __name__ == "__main__":
    main()"
