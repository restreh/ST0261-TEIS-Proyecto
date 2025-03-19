# Tienda de Ropa - Proyecto Django

Este proyecto es una aplicación web construida con Django para gestionar una tienda de ropa. Permite administrar productos, variantes (colores, tallas), imágenes, stock y órdenes de compra. La aplicación ofrece una interfaz pública para navegar, buscar y comprar productos (con carrito, lista de deseos y filtrado avanzado), y un panel de administración para gestionar el contenido y las órdenes.

---

## 🛠️ Requisitos

- **Python 3.10** (o superior)  
- **Django 4.x**  
- **Pip**  
- **Virtualenv** (recomendado)  

---

## 🛠️ Instalación

1. **Clonar el repositorio**  
   ```bash
   git clone https://github.com/restreh/ST0261-TEIS-Proyecto.git
   cd ST0261-TEIS-Proyecto
   ```

2. **Crear y activar un entorno virtual**  
   ```bash
   python -m venv env
   # En Linux/Mac:
   source env/bin/activate
   # En Windows:
   .\env\Scripts\activate
   ```

3. **Instalar dependencias**  
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**  
   Crea un archivo `.env` en la raíz del proyecto con la siguiente información (y otros datos sensibles necesarios):
   ```env
   DEBUG=True
   SECRET_KEY=tu_clave_secreta
   EMAIL_HOST=tu_host_de_correo
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=tu_email
   EMAIL_HOST_PASSWORD=tu_contraseña
   ```

   **Configuración del Correo Electrónico**
  Para enviar correos (por ejemplo, confirmaciones de pago), este proyecto utiliza Gmail. Sigue estos pasos para configurarlo correctamente:

    4.1. **Habilitar la verificación en dos pasos en tu cuenta de Google:**  
      Si aún no lo has hecho, activa la verificación en dos pasos desde la configuración de seguridad de tu cuenta de Google.

    4.2. **Generar una contraseña de aplicación:**  
      - Accede a la sección **"Contraseñas de aplicaciones"** en tu cuenta de Google.  
      - Selecciona "Otra (nombre personalizado)" y escribe un nombre (por ejemplo, "Django").  
      - Google te proporcionará una contraseña de 16 caracteres. Copia esa contraseña.

    4.3. **Configurar las variables de entorno en el archivo `.env`:**  
      Agrega la siguiente configuración en tu archivo `.env` (reemplazando los valores por los correspondientes a tu cuenta):
      ```env
      EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
      EMAIL_HOST=smtp.gmail.com
      EMAIL_PORT=587
      EMAIL_USE_TLS=True
      EMAIL_HOST_USER=tu_email@gmail.com
      EMAIL_HOST_PASSWORD=tu_contraseña_de_aplicación


5. **Aplicar migraciones**  
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Crear un superusuario**  
   ```bash
   python manage.py createsuperuser
   ```

7. **Ejecutar el servidor**  
   ```bash
   python manage.py runserver
   ```
   La aplicación estará disponible en [http://127.0.0.1:8000](http://127.0.0.1:8000).

---

## 📂 Estructura del Proyecto

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
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
├── templates/
│   └── store/
│       ├── base.html
│       ├── cart_detail.html
│       ├── login.html
│       ├── order_detail.html
│       ├── order_list.html
│       ├── product_detail.html
│       ├── product_list.html
│       ├── registration.html
│       ├── review_confirm_delete.html
│       ├── review_form.html
│       └── wish_list.html
├── static/
│   └── js/
│       └── product_detail.js
├── media/
├── manage.py
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

- **st0261_project/**: Configuración principal de Django.
- **store/**: Lógica de la aplicación (modelos, vistas, formularios, administración, etc.).
- **templates/store/**: Plantillas HTML para la interfaz pública y el panel de administración.
- **static/**: Archivos estáticos (CSS, JavaScript, imágenes de interfaz).  
- **media/**: Archivos subidos por usuarios (imágenes de productos).

---

## 🛠️ Funcionalidades y Uso

### 1. Registro e Inicio de Sesión

- **Registro:**  
  El usuario puede registrarse a través de un formulario. Los datos sensibles se gestionan mediante variables de entorno y se crea un perfil asociado automáticamente.

- **Inicio/Cierre de Sesión:**  
  La aplicación incluye rutas y vistas para iniciar y cerrar sesión. La barra de navegación se actualiza según el estado de autenticación.

---

### 2. Navegación de Productos

- **Listado de Productos:**  
  La página principal muestra tarjetas de productos con imagen y el precio.  
  - Incluye paginación y filtros (búsqueda, color, talla, género, rango de precios).

- **Detalle de Producto:**  
  La vista de detalle muestra:
  - Imagen principal.
  - Información del producto (descripción, materiales, guía de cuidado).
  - Sistema de selección de variante:  
    El usuario puede seleccionar color y talla. Al seleccionar solo color, se actualiza la imagen y el precio (con un mensaje de error si la talla elegida no está disponible).  
  - Formulario para agregar al carrito.

---

### 3. Carrito de Compras

- **Agregar Productos:**  
  Desde el listado o el detalle, el usuario puede agregar productos (o variantes) al carrito, especificando la cantidad.  
- **Visualizar y Editar Carrito:**  
  La vista de carrito muestra cada producto (con detalles de la variante, si aplica) en tarjetas uniformes, junto con el precio unitario y subtotal.  
- **Eliminar Productos:**  
  Permite ajustar la cantidad o eliminar productos por completo.
- **Generar Orden de Compra:**  
  Una vez revisado el carrito, el usuario puede proceder a comprar y generar una orden.

---

### 4. Lista de Deseados (Favoritos)

- **Agregar y Eliminar Favoritos:**  
  El usuario autenticado puede marcar productos como favoritos (mediante un icono de corazón) y visualizarlos en una página especial.  
- **Acceso a Detalle:**  
  En la lista de favoritos, los productos son clickeables para ver su detalle y, si lo desea, agregarlos al carrito.

---

### 5. Órdenes de Compra

- **Historial de Compras:**  
  La vista "Mis Compras" muestra las órdenes del usuario, con fecha, total, estado y dirección de envío.  
- **Pago y Cancelación:**  
  El usuario puede simular el pago de una orden pendiente y cancelar órdenes siempre que no se encuentren enviadas o entregadas.  
- **Generación de PDF:**  
  El usuario puede generar un PDF de la orden para impresión o archivo.

---

### 6. Panel de Administración

- **Gestión de Productos y Variantes:**  
  A través del panel de administración (accesible en `/admin`), se pueden crear y editar productos, variantes (colores, tallas) e imágenes.  
- **Gestión de Órdenes:**  
  El administrador puede ver y actualizar el estado de las órdenes (marcarlas como enviadas o entregadas) y, en el caso de marcar como enviado, descontar el stock de los productos.

---

### 7. Reseñas de Productos

- **Crear, Editar y Eliminar Reseñas:**  
  Solo los usuarios que han comprado el producto pueden dejar reseñas. Se proveen vistas para crear, editar y eliminar reseñas, y se muestran en la vista de detalle del producto.

---

## 📌 Notas Adicionales

- Para más información, visita:  
  [https://github.com/restreh/ST0261-TEIS-Proyecto](https://github.com/restreh/ST0261-TEIS-Proyecto) 

---