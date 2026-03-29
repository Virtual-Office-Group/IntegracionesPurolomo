import json, base64
import uuid
from azure.identity import DefaultAzureCredential
from azure.servicebus import ServiceBusClient, ServiceBusMessage, ServiceBusReceiveMode
from azure.servicebus.exceptions import ServiceBusError
from datetime import datetime, timezone, timedelta
import time
import os
import requests

script_dir = os.path.dirname(os.path.abspath(__file__))
print(script_dir)
#Variables para tomar tiempos
# Definimos el offset de UTC-4 (La Paz, Bolivia)
tz_caracas = timezone(timedelta(hours=-4))
# Obtenemos la hora actual en esa zona
now_caracas = datetime.now(tz_caracas)
AppSendTime=now_caracas.isoformat()


# Configuración (Usa tus Primary Connection Strings de cada cola)
#
ConnectStrSend = "{connection_string_sas}"
QueueInvHeaderLine = "recepcionalmacen"
QueueTransferHeaderLine = "pedidostransferencia"
QueueProductAjmt = "ajusteproducto"
QueueOut ="cola-salida" 

servicebus_client_out = ServiceBusClient.from_connection_string(conn_str=ConnectStrSend)
#my_correlation_id = str(uuid.uuid4()) # ID único para rastrear el mensaje
def get_service_bus_client(namespace_hostname):
    """
    Retorna un cliente autenticado mediante Entra ID (RBAC).
    :param namespace_hostname: El FQDN del namespace (ej: 'tu-espacio.servicebus.windows.net')
    """
    # DefaultAzureCredential gestiona el token automáticamente
    credential = DefaultAzureCredential()
    
    return ServiceBusClient(
        fully_qualified_namespace=namespace_hostname,
        credential=credential
    )

def crear_recepcion_inventario(send_correlation_id,payloadJSON,IdCompany,environment,Method):
    client = ServiceBusClient.from_connection_string(ConnectStrSend)
    with client.get_queue_sender(QueueInvHeaderLine) as sender:
        # Define aquí tu estructura de datos
        '''
        Para ver la estructura del ayload, ir a Postman.
                '''
        try:
            mensaje = ServiceBusMessage(payloadJSON,
                                        correlation_id=send_correlation_id, 
                                        application_properties={
                                        "environment":environment,
                                        "companyName":IdCompany,
                                        "RequestType": Method,  # Esta es tu propiedad personalizada
                                         }
                                        )
            sender.send_messages(message=mensaje)
            #mensaje.correlation_id = my_correlation_id # Sello de rastreo
            #print("="*40,"\n")
            print("✅Mensaje enviado correctamente\n")
            print(f"*Mensaje: {mensaje}\n*Cola: {QueueInvHeaderLine}\n*CorrelationID: {send_correlation_id} \n\n")
            #print("="*40,"\n")
        except ServiceBusError as e:
            print("❌ Error al enviar mensaje:", e)

    #return correlationId

def crear_transferencia(send_correlation_id,payloadJson,IdCompany,environment,Method,tipo="D"):
     client = ServiceBusClient.from_connection_string(ConnectStrSend)
     with client.get_queue_sender(QueueTransferHeaderLine) as sender:
        # Define aquí tu estructura de datos
        try:
            mensaje = ServiceBusMessage(payloadJson,
                                        correlation_id=send_correlation_id, 
                                        application_properties={
                                        "environment":environment,
                                        "companyName":IdCompany,
                                        "OperationType": Method, 
                                        "Warehousetype": tipo
                                        }
                                        )
            sender.send_messages(message=mensaje)
            AppSendTime=now_caracas.isoformat()
            #fecha_utc = datetime.now(timezone.utc)
            #timeStartQueue=fecha_utc.astimezone(ZoneInfo("America/Caracas")).isoformat()
            #mensaje.correlation_id = my_correlation_id # Sello de rastreo
            print("="*80,"\n")
            print(f"\n✅Mensaje enviado correctamente a la cola {QueueTransferHeaderLine}\n")
            print(f"✅Marca de tiempo de envio del Mensaje: {AppSendTime}")
            print(f"\n🟢Mensaje: {mensaje}\n🟢Cola: {QueueTransferHeaderLine}\n🟢Identificador de mensaje CorrelationId: {mensaje.correlation_id} \n\n")
            print("="*80,"\n")
        except ServiceBusError as e:
            print("\n❌ Error al enviar mensaje:", e)

def crear_ajuste_productos(send_correlation_id,payloadJson,IdCompany,environment,Method="POST"):
    client = ServiceBusClient.from_connection_string(ConnectStrSend)
    with client.get_queue_sender(QueueProductAjmt) as sender:
        # Define aquí tu estructura de datos
        '''payload = {
            "itemNo": "PROD002", 
            "entryType": "Positive Adjmt.", 
            "documentNo": "4875", 
            "locationCode": "PRINCIPAL", 
            "quantity": 40 
        }'''
        try:
            mensaje = ServiceBusMessage(payloadJson,correlation_id=send_correlation_id,
                                        application_properties={
                                        "environment":environment,
                                        "companyName":IdCompany,
                                        "OperationType": Method  # Esta es tu propiedad personalizada
                                        }
                                        
                                        )
            
            sender.send_messages(message=mensaje)
            now_caracas = datetime.now(tz_caracas)
            AppSendTime=now_caracas.isoformat()
            #mensaje.correlation_id = my_correlation_id # Sello de rastreo
            #print("="*40,"\n")
            print("✅Mensaje enviado correctamente\n")
            print(f"✅Marca de tiempo de envio del Mensaje: {AppSendTime}")
            print(f"✅Mensaje: {mensaje}\n*Cola: {QueueProductAjmt}\n*CorrelationID: {send_correlation_id} \n\n")
            #print("="*40,"\n")
        except ServiceBusError as e:
            print("❌ Error al enviar mensaje:", e) 

def obtener_resultados(msgcorrelation_id,operacion):
    print(f"Correlation ID del mensaje enviado {msgcorrelation_id}")
    timeout = 180  # 3 minutos de tiempo máximo total
    start_time = time.time()
    try:
        print("#######################################################################################################################")
        print(f"Monitoreando Cola de Salida:")
        with servicebus_client_out:
            receiver = servicebus_client_out.get_queue_receiver(queue_name=QueueOut, receive_mode=ServiceBusReceiveMode.PEEK_LOCK, prefetch_count=10)
            print(receiver)
            with receiver:
                MsgFound=False
                while (time.time() - start_time) < timeout and not MsgFound:
                    #obtenemos mensajes de 10 en 10 
                    received_messages = receiver.receive_messages(max_message_count=1, max_wait_time=1)
                    print(f"Mensajes tomados de la cola {len(received_messages)}")
                    for msg in received_messages:
                        #convertimos las propiedades del mensaje en diccionarios
                        props = msg.application_properties or {}
                        PropsSedMessage = {
                            (k.decode("utf-8") if isinstance(k, bytes) else k):
                            (v.decode("utf-8") if isinstance(v, bytes) else v)
                            for k, v in (props.items() if isinstance(props, dict) else [])
                        }
                        #PropsSedMessage = {k.decode('utf-8'): v.decode('utf-8') for k, v in msg.application_properties.items()}
                        body_bytes = b"".join(msg.body)
                        body_str = body_bytes.decode("utf-8")

                        #bloque de decodificación por este:
                        try:
                            # 1. Intentar decodificar Base64
                            decoded_bytes = base64.b64decode(body_str)
                            try:
                                # Intentar convertir esos bytes a texto (usando 'latin-1' si 'utf-8' falla)
                                decoded_text = decoded_bytes.decode("utf-8")
                            except UnicodeDecodeError:
                                decoded_text = decoded_bytes.decode("latin-1")
                            
                            data = json.loads(decoded_text)
                        except Exception:
                            # 2. Si falla lo anterior, intentar JSON directo
                            try:
                                data = json.loads(body_str)
                            except json.JSONDecodeError as je:
                                print(f"Error crítico: El cuerpo no es Base64 ni JSON válido. Detalle: {je}")
                                data = {"error": "invalid_format", "raw": body_str}


                        #if PropsSedMessage['idfromclient'] == msgcorrelation_id:
                        if PropsSedMessage.get('idfromclient') == msgcorrelation_id:
                            print(f"\n========================================================================================================================================")
                            print(f"\n#🟢 TU MENSAJE HA SIDO ENCONTRADO: {PropsSedMessage['idfromclient']}                                                                   #")
                            print(f"\n#🟢 TAMAÑO DEL MENSAJE: {PropsSedMessage['sizemessage'] } Bytes                                                                        #")
                            print(f"\n#🟢 TIEMPO DE ENVIO A LA COLA {AppSendTime}")                                                                                         
                            print(f"\n#🟢 TIEMPO INICIO EN LOGIC APP {PropsSedMessage['timereceived']} - TIEMPO SALIDA LOGIC APP {PropsSedMessage['timetoleave']}#") 
                            print(f"\n=======================================================================================================================================")
                            print(f'\n#🟢 Body: {json.dumps(data)}')
                            print(f"\n=======================================================================================================================================")
                            #fecha_utc = datetime.now(timezone.utc)
                            #timeTakeMsgQueue= fecha_utc.astimezone(ZoneInfo("America/Caracas"))
                            #timeTakeLogicaApp = PropsSedMessage["TIMEARRIVELOGICAPP"]
                            #timeleaveLogicApp = PropsSedMessage["TIMELEAVELOGICAPP"]
                            with open(script_dir+f"/Salida_JSON{operacion}.json",'w') as JsonWriteFile:
                                json.dump(data,JsonWriteFile,indent = 4)
                            receiver.complete_message(msg)
                            MsgFound = True
                            break  # salir después de encontrar mi respuesta
                        else:
                            print(f"\n🔴No existen mensaje en la Cola {QueueOut} con Correlation Id  {msgcorrelation_id}")
                            print(f"\n🔴Mensaje abandonado en la cola: {msg.correlation_id}")
                            receiver.abandon_message(msg)
                            print(f'\nPropiedades: {msg.application_properties}')
                            print(f'\nBody: {data}')
                            #print(f'\n{msg}')

    except ServiceBusError as e:
        print(e)

def creacion_payload_desde_archivo(IdCompany,archivoJson):
    try:
        newJsonReg={}
        with open (archivoJson,'r') as JsonToProcess:
            JsonRegLists = json.load(JsonToProcess)
            print(JsonRegLists)
            #Cargar su contenido y crear un diccionario
        if "lines" not in JsonRegLists:
            print("===================VAMOS A PROCESAR UN ENCABEZADO=====================")    
            for k,v in JsonRegLists.items():
                newJsonReg[k] = v
            #newJsonReg['companyName']=str(IdCompany)
            #newJsonReg['environment']='TEST'
        else:
            print("===================VAMOS A PROCESAR LINEAS=====================")    
            for k,v in JsonRegLists.items():
                newJsonReg[k] = v
            #newJsonReg['companyName']=str(IdCompany)
            #newJsonReg['environment']='TEST'
        print(f"Objeto Diccionario Python: {newJsonReg}")    
        print(f"Nueva arreglo Json: {json.dumps(newJsonReg,indent=4)}")
        payload = json.dumps(newJsonReg,indent=4)
        return payload
    except TypeError as e:
        print(e) 

def crear_payload_actualizacion(tipo,registro):
    if tipo=='R':
        payload = json.loads(registro)
        
    if tipo=='T':
        payload = json.loads(registro)

def entorno_pruebas():
    print(f"\nSeleccione el entorno de pruebas de Business Central:")
    print("1-. CRONUS ES" )
    print("2-. PRUEBA BC")
    print("3-. DEMO")
 
    CompanySelect=int(input('Seleccione una opcion:'))
    if CompanySelect==1:
       CompaniaTest="9c2a3721-0c80-ef11-ac21-0022483842ea" #CRONUS ES
       env="TEST"
    elif CompanySelect==2:
       CompaniaTest="41cc1c74-5021-f011-9af7-000d3ac04986" #PRUEBA BC
       env="TEST"
    elif CompanySelect==3:
        CompaniaTest="db22931c-25f2-f011-8405-000d3a88d306" #DEMO
        env="DEMO"

    return CompaniaTest,env

def probar_payloads(IdCompany):
    JsonOption=9
    while JsonOption != 0:
        print(f"\nSELECCIONE EL PAYLOAD EN FORMATO JSON A PROBAR :")
        print("1-. Recepcion Inventario")
        print("2-. Pedidos de Transferencia" )
        print("0-. Salir")

        JsonOption=int(input('Seleccione una opcion:'))
        if JsonOption==1:
            creacion_payload_desde_archivo(IdCompany,script_dir+"/RecepcionInventario.json")
        elif JsonOption==2:
            creacion_payload_desde_archivo(IdCompany,script_dir+"/TransferenciaPedidos.json")

   
if __name__ == "__main__":
    resp=10
    CompaniaTest=None
    Environment=None
    while resp != 0:

        print(f"\n1-. Seleccionar el entorno de Pruebas. Entorno de Prueba:{CompaniaTest} ({Environment})")
        print(f"2-. [C]rear [A]ctualizar Recepcion Almacen.")
        print(f"3-. [C]rear [A]ctualizar Transferencia Pedido.")
        print(f"4-. [C]rear [A]ctualizar Transferencia Pedido Con Envio de Almacen.")
        print(f"5-. [C]rear [A]ctualizar Transferencia Pedido Con Picking.")
        print(f"6-. Crear Ajuste de Productos" )    
        print(f"7-. Probar JSON payload")
        print(f"0-. Salir.")
        Opciones = input(f"Seleccione una Opcion Numeros[0,1,2,3,4,5] para para funcionalidad [C ò c] para metodo POST y [A ó a] para PATCH:")
        
        resp=int(list(Opciones)[0])
        if len(Opciones)>1:
            Operacion=str(list(Opciones)[1])
        
            if Operacion=='A':
                Metodo = "PATCH"
            elif Operacion=='C':
                Metodo = "POST"
        else:
            print("No se ha seleccionado una operación válida, se tomará por defecto la operación de CREAR[C=POST]")
            Metodo = "POST"

        if resp==0:
           break   #Salir

        if resp==1:
            CompaniaTest,Environment=entorno_pruebas()
        
        if resp == 2:
            if CompaniaTest != None:
                correlationId = str(uuid.uuid4()) # ID único para rastrear el mensaje
                PayloadFile = creacion_payload_desde_archivo(CompaniaTest,script_dir+"/RecepcionInventario.json")
                #IdBC="491870d0-0c14-f111-8341-002248d31bd2"
                IdBC=""
                crear_recepcion_inventario(correlationId,PayloadFile,CompaniaTest,Environment,Metodo)
                obtener_resultados(correlationId,"RecepcionInventario")
            else:
                print("❌ ******Debe seleccionar un entorno de Prueba de BC******")
        elif resp == 3:
            if CompaniaTest != None:            
                correlationId = str(uuid.uuid4())
                PayloadFile=creacion_payload_desde_archivo(CompaniaTest,script_dir+"/transferenciaPedidos.json")
                crear_transferencia(correlationId,PayloadFile,CompaniaTest,Environment,Metodo)
                obtener_resultados(correlationId,"TransferenciaPedidos")

            else:
                print("❌ ******Debe seleccionar un entorno de Prueba de BC*****")
        elif resp == 4:
            if CompaniaTest != None:            
                correlationId = str(uuid.uuid4())
                PayloadFile=creacion_payload_desde_archivo(CompaniaTest,script_dir+"/transferenciaPedidos.json")
                crear_transferencia(correlationId,PayloadFile,CompaniaTest,Environment,Metodo)
                obtener_resultados(correlationId,"TransferenciaPedidosEnviosAlmacen")

            else:
                print("❌ ******Debe seleccionar un entorno de Prueba de BC*****")
            # curl --location --request POST 'https://api.businesscentral.dynamics.com/v2.0//DEMO/api/virtualOfficeGroup/integration/v1.0/companies(db22931c-25f2-f011-8405-000d3a88d306)/transferOrders(bba7deb9-7a21-f111-8340-7ced8da8a20f)/Microsoft.NAV.createWarehouseShipment'
        elif resp == 5:
            print("POR DEFINIR PICKING")
            #curl --location --request POST 'https://api.businesscentral.dynamics.com/v2.0//DEMO/api/virtualOfficeGroup/integration/v1.0/companies(db22931c-25f2-f011-8405-000d3a88d306)/warehouseShipmentLines(7c8e51d4-7a21-f111-8340-7ced8da8a20f)/Microsoft.NAV.createPicking'
        elif resp == 6:
            if CompaniaTest != None:            
                correlationId = str(uuid.uuid4())
                PayloadFile=creacion_payload_desde_archivo(CompaniaTest,script_dir+"/ajusteProductos.json")
                crear_ajuste_productos(correlationId,PayloadFile,CompaniaTest,Environment,Metodo)
                obtener_resultados(correlationId,"AjusteProducto")
        elif resp == 7:
            if CompaniaTest != None:            
                #correlationId = str(uuid.uuid4())
                probar_payloads(CompaniaTest)
            else:
                print("❌ ******Debe seleccionar un entorno de Prueba de BC*****")
   

