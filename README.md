# Tienda de Ropa - Proyecto Django

Este proyecto es una aplicación web construida con Django que permite gestionar productos, variantes de producto, imágenes y stock para una tienda de ropa. Se incluye una interfaz pública para visualizar los productos en tarjetas y un panel de administración para gestionar el contenido.

## 🛠️ Requisitos

Antes de comenzar, asegúrate de tener instalados los siguientes elementos:

- **Python 3.10** (o superior)
- **Django 4.x**
- **Pip** (gestor de paquetes de Python)
- **Virtualenv** (opcional pero recomendado)

## 🛠️ Instalación

1. **Clonar el repositorio:**

   ```bash
   git clone https://github.com/restreh/ST0261-TEIS-Proyecto.git
   cd ST0261-TEIS-Proyecto
   ```

2. **Crear y activar un entorno virtual:**

   ```bash
   python -m venv env
   # En Linux/Mac:
   source env/bin/activate
   # En Windows:
   .\env\Scripts\activate
   ```

3. **Instalar dependencias:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno:**

   Crea un archivo `.env` en la raíz del proyecto y añade tus configuraciones básicas. Por ejemplo:

   ```
   DEBUG=True
   SECRET_KEY=tu_clave_secreta
   ```

5. **Aplicar migraciones:**

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Crear un superusuario para acceder al panel de administración:**

   ```bash
   python manage.py createsuperuser
   ```

7. **Ejecutar el servidor de desarrollo:**

   ```bash
   python manage.py runserver
   ```

La aplicación estará disponible en [http://127.0.0.1:8000](http://127.0.0.1:8000).

## 📂 Estructura del Proyecto

La estructura básica del proyecto es la siguiente:

```
Tienda de Ropa/
├── st0261_project/ 
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── store/
│   ├── migrations/
│   ├── admin.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
├── templates/
│   └── store/
│       ├── product_list.html
├── media/
├── manage.py
├── .env
├── .gitignore
├── requirements.txt
```

*Nota:* La carpeta `static` no se utiliza en este momento.

## 🛠️ Funcionalidades Implementadas

- **Agregar Productos:**  
  Desde el panel de administración puedes crear productos, variantes (color, talla) y subir imágenes.  
  - **Generación Automática de SKU:** Cada variante tiene un SKU generado automáticamente en función del producto, color y talla.
  
- **Visualizar Productos:**  
  La página pública muestra los productos en tarjetas con imagen, nombre, descripción y precio.

## 🧩 Cómo Agregar un Producto

1. **Acceder al panel de administración:**  
   Ingresa a [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) e inicia sesión con tus credenciales de superusuario.

2. **Crear un nuevo producto:**  
   - Ve a **Productos** y selecciona **Agregar producto**.
   - Completa los campos requeridos: nombre, género, precio, descripción, materiales y guía de cuidado.

3. **Agregar variantes del producto:**  
   - Desde el formulario de creación/edición del producto, agrega variantes (color, talla, stock, precio especial).
   - Si es necesario, agrega imágenes a cada variante a través de la edición individual o utilizando nested inlines (si decides implementarlos).

4. **Guardar los cambios:**  
   Haz clic en **Guardar** para que el producto y sus variantes se registren en la base de datos.

---

Para más detalles y futuras actualizaciones, visita el repositorio en:  
[https://github.com/restreh/ST0261-TEIS-Proyecto](https://github.com/restreh/ST0261-TEIS-Proyecto)


---
