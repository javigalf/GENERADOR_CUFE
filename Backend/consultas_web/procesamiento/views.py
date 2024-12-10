from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework import status
import os
import pandas as pd
from django.conf import settings
from datetime import datetime
from threading import Thread
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import PyPDF2
from django.http import FileResponse
from anticaptchaofficial.turnstileproxyless import turnstileProxyless  # Importar AntiCaptcha
import uuid  # Para generar IDs únicos
import json  # Para guardar el progreso en archivos JSON
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from .models import UserActivityLog
from rest_framework import generics, serializers
from django.contrib.auth.models import User

API_KEY_ANTICAPTCHA = "43d46b3bf5c7017b20182e5ffa05f184"  # Reemplaza con tu clave real

class UploadFileView(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = request.user
            ahora = datetime.now()
            mes_actual = ahora.month
            año_actual = ahora.year

            # Obtener o crear el registro mensual (sin filtrar por fecha_y_hora_deslogueo, para evitar duplicados)
            activity_log, created = UserActivityLog.objects.get_or_create(
                usuario=user,
                mes=mes_actual,
                año=año_actual,
                defaults={'fecha_y_hora_logueo': timezone.now()}
            )

            file = request.FILES.get('file')
            if not file:
                return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

            # Generar un ID único para la tarea
            task_id = str(uuid.uuid4())

            # Crear directorios específicos para la tarea
            task_dir = os.path.join(settings.MEDIA_ROOT, "tasks", task_id)
            upload_dir = os.path.join(task_dir, "uploads")
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, file.name)

            # Guardar el archivo temporalmente
            with open(file_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

            # Cargar el archivo y calcular el número total de registros
            try:
                df = pd.read_excel(file_path)
                total_records = len(df)
            except Exception as e:
                return Response({"error": f"Error leyendo el archivo: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

            # Inicializar el progreso
            progress_data = {
                "progress": 0,
                "total_records": total_records,
                "start_time": datetime.now().isoformat()
            }

            # Guardar el progreso inicial
            progress_file = os.path.join(task_dir, "progress.json")
            with open(progress_file, 'w') as f:
                json.dump(progress_data, f)

            # Procesar en segundo plano, pasando mes_actual y año_actual
            Thread(target=self.safe_process_file, args=(file_path, task_id, user, mes_actual, año_actual, total_records)).start()

            return Response({"message": "Archivo subido exitosamente", "total_records": total_records, "task_id": task_id})

        except Exception as e:
            print(f"Exception in UploadFileView.post: {e}")
            return Response({"error": f"Ocurrió un error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def safe_process_file(self, file_path, task_id, user, mes_actual, año_actual, total_records):
        try:
            self.process_file(file_path, task_id, user, mes_actual, año_actual, total_records)
        except Exception as e:
            print(f"Error durante el procesamiento del archivo: {str(e)}")

    def process_file(self, file_path, task_id, user, mes_actual, año_actual, total_records):
        try:
            df_original = pd.read_excel(file_path)
            if 'CUFE/CUDE' not in df_original.columns:
                raise ValueError("El archivo no contiene la columna 'CUFE/CUDE' necesaria.")
        except Exception as e:
            print(f"Error al leer el archivo: {str(e)}")
            return

        # Crear DataFrame con las columnas necesarias
        columnas_nuevas = ['Cufe','Tipo de Documento','Serie','Folio','Fecha de Emisión','NIT Emisor','Nombre Emisor','NIT Receptor','Nombre Receptor','Subtotal','IVA','Total','Eventos','Forma de Pago','Link','Descarga PDF']
        df_nuevo = pd.DataFrame(columns=columnas_nuevas)
        df_nuevo['Cufe'] = df_original['CUFE/CUDE']
        df_nuevo['Tipo de Documento'] = df_original.get('Tipo de documento', '')
        df_nuevo['Folio'] = df_original.get('Folio', '')
        df_nuevo['Serie'] = df_original.get('Prefijo', '')
        df_nuevo['Fecha de Emisión'] = df_original.get('Fecha Emisión', '')
        df_nuevo['NIT Emisor'] = df_original.get('NIT Emisor', '')
        df_nuevo['Nombre Emisor'] = df_original.get('Nombre Emisor', '')
        df_nuevo['NIT Receptor'] = df_original.get('NIT Receptor', '')
        df_nuevo['Nombre Receptor'] = df_original.get('Nombre Receptor', '')

        task_dir = os.path.join(settings.MEDIA_ROOT, "tasks", task_id)
        download_dir = os.path.join(task_dir, "downloads")
        os.makedirs(download_dir, exist_ok=True)

        # Limpiar descargas
        for f in os.listdir(download_dir):
            if f.endswith('.pdf') or f.endswith('.crdownload'):
                os.remove(os.path.join(download_dir, f))

        chrome_options = Options()
        prefs = {
            'download.default_directory': download_dir,
            'plugins.always_open_pdf_externally': True,
            'download.prompt_for_download': False,
            'download.directory_upgrade': True
        }

        chrome_options.add_experimental_option('prefs', prefs)
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")

        def iniciar_driver():
            return webdriver.Chrome(options=chrome_options)

        def wait_for_download(download_dir, timeout=30):
            import glob
            seconds = 0
            dl_wait = True
            while dl_wait and seconds < timeout:
                time.sleep(1)
                dl_wait = False
                files = glob.glob(os.path.join(download_dir, '*'))
                for fname in files:
                    if fname.endswith('.crdownload'):
                        dl_wait = True
                seconds += 1
            return not dl_wait

        def resolver_captcha_turnstile(pageurl, sitekey):
            solver = turnstileProxyless()
            solver.set_verbose(1)
            solver.set_key(API_KEY_ANTICAPTCHA)
            solver.set_website_url(pageurl)
            solver.set_website_key(sitekey)
            return solver.solve_and_return_solution()

        driver = iniciar_driver()
        total_registros = len(df_nuevo)
        progress = 0

        for index, row in df_nuevo.iterrows():
            cufe = row['Cufe']
            url = f'https://catalogo-vpfe.dian.gov.co/document/searchqr?documentKey={cufe}'
            df_nuevo.at[index, 'Link'] = url

            eventos = []
            reintentos = 3
            while reintentos > 0:
                try:
                    driver.get(url)
                    sitekey = "0x4AAAAAAAg1WuNb-OnOa76z"
                    token = resolver_captcha_turnstile(url, sitekey)

                    if token:
                        # Resolver captcha
                        captcha_response_field = WebDriverWait(driver, 20).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "input[id^='cf-chl-widget']"))
                        )
                        driver.execute_script(f'arguments[0].value="{token}";', captcha_response_field)

                        buscar_button = WebDriverWait(driver, 20).until(
                            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Buscar")]'))
                        )
                        buscar_button.click()

                        # Esperar la tabla
                        WebDriverWait(driver, 20).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".documents-table tbody"))
                        )
                        print(f"[LOG] Tabla encontrada para el CUFE: {cufe}")

                        # Extraer filas de la tabla
                        filas_tabla = driver.find_elements(By.CSS_SELECTOR, ".documents-table tbody tr")
                        print(f"[LOG] CUFE: {cufe} - Total filas encontradas en la tabla: {len(filas_tabla)}")

                        for fila in filas_tabla:
                            try:
                                codigo = fila.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text
                                if re.match(r'^\d{3}$', codigo):
                                    eventos.append(codigo)
                                    print(f"[LOG] Código válido encontrado: {codigo}")
                            except Exception as e:
                                print(f"[ERROR] No se pudo extraer un código en una fila: {e}")

                        if eventos:
                            df_nuevo.at[index, 'Eventos'] = ", ".join(eventos)
                            print(f"[LOG] Eventos registrados para el CUFE {cufe}: {', '.join(eventos)}")
                        else:
                            df_nuevo.at[index, 'Eventos'] = "sin evento"
                            print(f"[LOG] No se encontraron eventos para el CUFE {cufe}.")

                        # Extraer datos del PDF
                        descargar_pdf = WebDriverWait(driver, 20).until(
                            EC.presence_of_element_located((By.XPATH, '//a[@class="downloadPDFUrl"]'))
                        )
                        href = descargar_pdf.get_attribute('href')
                        full_link = f"https://catalogo-vpfe.dian.gov.co{href.replace('amp;', '')}" if href.startswith('/') else href.replace('amp;', '')
                        df_nuevo.at[index, 'Descarga PDF'] = full_link

                        descargar_pdf.click()

                        # Esperar que termine descarga
                        if wait_for_download(download_dir):
                            pdf_files = [f for f in os.listdir(download_dir) if f.endswith('.pdf')]
                            if pdf_files:
                                pdf_path = os.path.join(download_dir, pdf_files[0])
                            else:
                                print(f"[ERROR] No se encontró el PDF para CUFE {cufe}")
                                df_nuevo.at[index, 'Subtotal'] = 'Error al descargar PDF'
                                df_nuevo.at[index, 'IVA'] = ''
                                df_nuevo.at[index, 'Total'] = ''
                                df_nuevo.at[index, 'Forma de Pago'] = ''
                                break
                        else:
                            print(f"[ERROR] Descarga del PDF para CUFE {cufe} excedió el tiempo")
                            df_nuevo.at[index, 'Subtotal'] = 'Descarga excedió tiempo'
                            df_nuevo.at[index, 'IVA'] = ''
                            df_nuevo.at[index, 'Total'] = ''
                            df_nuevo.at[index, 'Forma de Pago'] = ''
                            break

                        # Leer y extraer datos del PDF
                        try:
                            with open(pdf_path, 'rb') as pdf_file:
                                reader = PyPDF2.PdfReader(pdf_file)
                                contenido = ''.join(page.extract_text() for page in reader.pages)

                            # Regex para extraer datos
                            subtotal_match = re.search(r'Subtotal\s*[:=]?\s*([\d.,]+)', contenido)
                            iva_match = re.search(r'Total impuesto\s*\(=\)?\s*([\d.,]+)', contenido)
                            total_match = re.search(r'Total factura\s*\(=\)[^\d]*(\d[\d.,]+)', contenido)
                            forma_pago_match = re.search(r'Forma de pago:\s*(\w+)', contenido)

                            df_nuevo.at[index, 'Subtotal'] = subtotal_match.group(1) if subtotal_match else 'No encontrado'
                            df_nuevo.at[index, 'IVA'] = iva_match.group(1) if iva_match else 'No encontrado'
                            df_nuevo.at[index, 'Total'] = total_match.group(1) if total_match else 'No encontrado'
                            df_nuevo.at[index, 'Forma de Pago'] = forma_pago_match.group(1) if forma_pago_match else 'No encontrado'

                        except Exception as e:
                            print(f"[ERROR] Error al extraer datos del PDF para CUFE {cufe}: {e}")
                            df_nuevo.at[index, 'Subtotal'] = 'Error al extraer datos'
                            df_nuevo.at[index, 'IVA'] = ''
                            df_nuevo.at[index, 'Total'] = ''
                            df_nuevo.at[index, 'Forma de Pago'] = ''

                        finally:
                            if os.path.exists(pdf_path):
                                os.remove(pdf_path)

                        # Si todo fue exitoso, sal del bucle reintentos
                        break

                    else:
                        print(f"[ERROR] Error al resolver el captcha para CUFE {cufe}")
                        reintentos -= 1

                except Exception as e:
                    print(f"[ERROR] Error al procesar el CUFE {cufe}: {e}")
                    reintentos -= 1
                    print("[LOG] Reiniciando el driver...")
                    driver.quit()
                    driver = iniciar_driver()

            progress += 1
            print(f"Registro procesado: {progress}/{total_registros}")

            # Actualizar progreso
            progress_data = {
                "progress": progress,
                "total_records": total_records,
                "start_time": datetime.now().isoformat()
            }
            progress_file = os.path.join(task_dir, "progress.json")
            with open(progress_file, 'w') as f:
                json.dump(progress_data, f)

        driver.quit()

        # Guardar resultado final
        result_path = os.path.join(task_dir, "processed_file.xlsx")
        df_nuevo.to_excel(result_path, index=False)
        print(f"Archivo procesado guardado en {result_path}")

        # Actualizar cantidad_registros_gestionados del mes
        activity_log = UserActivityLog.objects.get(
            usuario=user,
            mes=mes_actual,
            año=año_actual
        )
        activity_log.cantidad_registros_gestionados += total_records
        activity_log.save()

class ProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        task_dir = os.path.join(settings.MEDIA_ROOT, "tasks", task_id)
        progress_file = os.path.join(task_dir, "progress.json")
        if os.path.exists(progress_file):
            with open(progress_file, 'r') as f:
                progress_data = json.load(f)
            elapsed_time = (datetime.now() - datetime.fromisoformat(progress_data["start_time"])).total_seconds()
            return Response({
                "progress": progress_data["progress"],
                "total_records": progress_data["total_records"],
                "elapsed_time": elapsed_time
            })
        else:
            return Response({"error": "Task not found or progress not available"}, status=status.HTTP_404_NOT_FOUND)

class DownloadFileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        task_dir = os.path.join(settings.MEDIA_ROOT, "tasks", task_id)
        result_path = os.path.join(task_dir, "processed_file.xlsx")
        if os.path.exists(result_path):
            try:
                response = FileResponse(
                    open(result_path, 'rb'),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = f'attachment; filename="archivo_final_{task_id}.xlsx"'
                return response
            except Exception as e:
                return Response({"error": f"Error al servir el archivo: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"error": "Archivo no encontrado"}, status=status.HTTP_404_NOT_FOUND)

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        # Ya no usamos fecha_y_hora_deslogueo en el filtro, pues ya no depende de eso la unicidad
        # Si aún deseas usarlo para marcar cuando se cierra sesión, puedes actualizar el registro del mes actual.
        ahora = datetime.now()
        mes_actual = ahora.month
        año_actual = ahora.year
        try:
            activity_log = UserActivityLog.objects.get(usuario=user, mes=mes_actual, año=año_actual)
            activity_log.fecha_y_hora_deslogueo = timezone.now()
            activity_log.save()
        except UserActivityLog.DoesNotExist:
            # Si no existe registro para este mes, no pasa nada
            pass

        return Response({"message": "Sesión cerrada exitosamente"}, status=status.HTTP_200_OK)
