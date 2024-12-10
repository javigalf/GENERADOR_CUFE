import React, { useState, useEffect } from "react";
import axios from "axios";
import "./FileProcessor.css";

const FileProcessor = ({ token, setToken }) => {
  const [file, setFile] = useState(null);
  const [taskId, setTaskId] = useState(null); // Nuevo estado para almacenar el task_id
  const [progress, setProgress] = useState(0);
  const [totalRecords, setTotalRecords] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const uploadFile = async () => {
    if (!file) {
      alert("¡Por favor, selecciona un archivo primero!");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post(
        "http://localhost:8000/api/upload/",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
            Authorization: `Bearer ${token}`,
          },
        }
      );
      setTotalRecords(response.data.total_records);
      setTaskId(response.data.task_id);
      setIsProcessing(true);
    } catch (error) {
      console.error("Error al subir el archivo:", error);
    }
  };

  const logout = async () => {
    try {
      await axios.post(
        "http://localhost:8000/api/logout/",
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      setToken(null); // Esto borrará el token del estado y del localStorage
    } catch (error) {
      console.error("Error al cerrar sesión:", error);
      setToken(null);
    }
  };

  useEffect(() => {
    let interval; // Declarar el intervalo fuera del bloque if
    if (isProcessing && taskId) {
      // Verificar que taskId está disponible
      interval = setInterval(async () => {
        try {
          const response = await axios.get(
            `http://localhost:8000/api/progress/${taskId}/`,
            {
              headers: {
                Authorization: `Bearer ${token}`,
              },
            }
          );
          setProgress(response.data.progress);
          setElapsedTime(response.data.elapsed_time);

          if (response.data.progress >= response.data.total_records) {
            setIsProcessing(false);
            clearInterval(interval);
          }
        } catch (error) {
          console.error("Error al obtener el progreso:", error);
          clearInterval(interval);
        }
      }, 1000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isProcessing, taskId, token]); // Agregar token como dependencia

  const downloadFile = async () => {
    if (!taskId) {
      alert("El ID de la tarea no está disponible.");
      return;
    }
    try {
      const response = await axios.get(
        `http://localhost:8000/api/download/${taskId}/`,
        {
          responseType: "blob",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "processed_file.xlsx");
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error("Error al descargar el archivo:", error);
    }
  };

  return (
    <div className="file-processor">
      <h1>Procesador de Archivos</h1>
      <button onClick={logout}>Cerrar Sesión</button>
      <input type="file" onChange={handleFileChange} />
      <button onClick={uploadFile}>Subir y Procesar</button>
      {isProcessing && (
        <>
          <p>
            Procesando: {progress}/{totalRecords}
          </p>
          <p>Tiempo transcurrido: {Math.floor(elapsedTime)} segundos</p>
        </>
      )}
      {progress === totalRecords && totalRecords > 0 && (
        <button onClick={downloadFile}>Descargar Resultados</button>
      )}
    </div>
  );
};

export default FileProcessor;