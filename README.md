# Tienda de Ropa - Proyecto Django

Este proyecto es una aplicación web construida con Django que permite gestionar productos, variantes de producto, imágenes y stock para una tienda de ropa. Ofrece una interfaz pública para navegar y comprar productos (con carrito y lista de deseos) y un panel de administración para gestionar el contenido y las órdenes de compra.

## 🛠️ Requisitos

- **Python 3.10** (o superior)  
- **Django 4.x**  
- **Pip** (gestor de paquetes de Python)  
- **Virtualenv** (opcional, pero recomendado)

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
   Crea un archivo `.env` en la raíz del proyecto con información como:
   ```
   DEBUG=True
   SECRET_KEY=tu_clave_secreta
   ```

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
   Visita [http://127.0.0.1:8000](http://127.0.0.1:8000) para ver la aplicación en funcionamiento.

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
│       ├── order_list.html
│       ├── product_list.html
│       ├── registration.html
│       ├── wish_list.html
│       └── ...
├── media/
├── manage.py
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

- **st0261_project/**: Configuración principal de Django.  
- **store/**: Contiene la lógica de la app (modelos, vistas, formularios, admin, etc.).  
- **templates/store/**: Plantillas HTML para las distintas secciones de la tienda.  
- **media/**: Carpeta para las imágenes de los productos.  

---

## 🛠️ Funcionalidades y Uso

### 1. Registro e Inicio de Sesión

- **Registrarse**  
  Ve a la página de registro o haz clic en “Registrarse” en la barra de navegación. Completa el formulario y envíalo.  
- **Iniciar Sesión**  
  Haz clic en “Iniciar sesión” en la barra de navegación e ingresa tus credenciales.  
- **Cerrar Sesión**  
  Si ya iniciaste sesión, verás un enlace de “Cerrar sesión” que te permite salir.

### 2. Carrito de Compras

- **Agregar al Carrito**  
  Desde la lista de productos, elige la variante (si aplica), la cantidad y haz clic en “Añadir al carrito”.  
- **Ver Carrito**  
  Haz clic en “Carrito” en la barra de navegación. Verás los productos agregados, su cantidad y el subtotal.  
- **Eliminar del Carrito**  
  Dentro del carrito, puedes ajustar la cantidad o eliminar el producto por completo.  
- **Comprar**  
  Si iniciaste sesión, verás un botón de “Comprar” para generar la orden de compra.

### 3. Lista de Deseados (Favoritos)

- **Agregar a Favoritos**  
  Inicia sesión. Junto al botón de “Añadir al carrito” verás un icono de corazón para añadir el producto a tu lista de deseados.  
- **Ver Favoritos**  
  En la barra de navegación aparecerá “Favoritos”. Allí verás todos los productos que marcaste como deseados.  
- **Eliminar de Favoritos**  
  En la lista de deseados, cada producto tendrá un botón para quitarlo.

### 4. Órdenes de Compra

- **Mis Compras**  
  Si iniciaste sesión, verás “Mis Compras” en la barra de navegación. Allí se listan todas tus órdenes con fecha, total y estado.  
- **Pagar**  
  Si la orden está pendiente, puedes hacer clic en “Pagar ahora” para simular el pago.  
- **Cancelar**  
  Podrás cancelar la orden si no ha sido marcada como “Enviada” o “Entregada”.  

### 5. Panel de Administración

- **Acceso**  
  Ingresa a [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) y usa tus credenciales de superusuario.  
- **Gestión de Productos**  
  Crea productos, variantes (color, talla, stock) e imágenes.  
- **Gestión de Órdenes de Compra**  
  Verás todas las órdenes, podrás marcarlas como “Enviadas” (descontando stock) o “Entregadas”, siempre que no estén canceladas.

---

## 🧩 Cómo Agregar un Producto

1. **Acceder al Admin**  
   Ingresa a [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) e inicia sesión.  
2. **Crear Producto**  
   Ve a **Productos** → **Agregar producto** y llena los campos.  
3. **Añadir Variantes**  
   Indica color, talla, stock, precio especial, etc.  
4. **Subir Imágenes**  
   Sube las imágenes que desees para cada variante.  
5. **Guardar**  
   Al guardar, verás tu producto en la lista.

---

## 📌 Notas Finales

- Para cualquier usuario creado antes de la implementación del perfil, asegúrate de asignarle un perfil.  
- Configura **MEDIA_URL** y **MEDIA_ROOT** en `settings.py` para mostrar imágenes de productos.  
- Para más información, visita:  
  [https://github.com/restreh/ST0261-TEIS-Proyecto](https://github.com/restreh/ST0261-TEIS-Proyecto) 

---