# WRO FUTURE ENGINEEERS 2026 
CYBERBOTS 


CyberBots es un equipo de robótica que participa en WRO Future Engineers 2026, donde desarrollamos vehículos autónomos capaces de interpretar su entorno y tomar decisiones de forma independiente.


Este repositorio documenta nuestro proceso de desarrollo, desde el diseño y ensamblaje hasta la programación, las pruebas y las mejoras realizadas durante el proyecto.



-[1 Nuestro equipo](#1-nuestro-equipo)

-[2 Descripcion del proyecto](#2-descripcion-del-proyecto) 

-[2.1 Acerca del proyecto](#2.1-acerca-del-proyecto)
-[3. Gestión de la movilidad](#3.-gestion-de-movilidad)





## 1 Nuestro equipo 

Somos un equipo conformado por dos estudiantes guatemaltecos que compartimos el interés por la robótica, la tecnología y la innovación. A lo largo del proyecto, hemos trabajado de manera colaborativa, aportando nuestras habilidades y conocimientos en las diferentes áreas necesarias para desarrollar nuestro vehículo.

INTEGRANTES 

Stefany Andrea Tobar de Paz

EDAD: 16 años

Estudiante guatemalteca del Colegio Villa Real Atlántico 1. Actualmente cursa el grado de cuarto bachillerato en Ciencias y Letras con Orientación en Computación. Se caracteriza por ser responsable, organizada y comprometida con el trabajo en equipo. Dentro del proyecto, está a cargo principalmente de la programación, electrónica y documentación del proyecto.

Jason Arturo Carrera Garrido

EDAD: 17 años

Estudiante guatemalteco del Colegio Villa Real Atlántico 1. Actualmente cursa el grado de cuarto bachillerato en Ciencias y Letras con Orientación en Diseño Gráfico. Se caracteriza por su creatividad, disposición para colaborar y capacidad para aportar al trabajo en equipo. Está encargado principalmente del diseño y desarrollo visual del proyecto.




## 2 Descripcion del Proyecto 
## 2.1 Acerca del Proyecto 

Este proyecto consiste en el desarrollo de un vehículo robótico autónomo diseñado para enfrentar los distintos retos de navegación y detección de obstáculos de la competencia WRO Future Engineers. A través de este desafío, buscamos poner en práctica nuestros conocimientos de robótica, electrónica y programación para crear una solución capaz de desenvolverse de manera autónoma en una pista de competición.

La idea surge de nuestro interés por explorar nuevas posibilidades en la ingeniería y convertir los desafíos técnicos en oportunidades para innovar, experimentar y aprender. Como equipo, trabajamos en el diseño e integración de los diferentes componentes, buscando mejorar el funcionamiento del robot mediante pruebas, análisis de resultados y ajustes continuos.

El sistema está basado en una Raspberry Pi 4, encargada del procesamiento principal, junto con una cámara HuskyLens, que permite identificar visualmente los elementos del entorno. Además, incorpora un sensor LIDAR para obtener información sobre las distancias y contribuir a una navegación más segura y precisa. La combinación de estos componentes busca fortalecer la capacidad del robot para interpretar su entorno y responder adecuadamente ante los obstáculos presentes en la pista.

Durante el desarrollo, documentamos los avances, las configuraciones y las soluciones implementadas con el propósito de mantener un registro organizado del proceso de construcción y programación.

Nuestro objetivo es desarrollar un robot autónomo que combine precisión, capacidad de respuesta y eficiencia, demostrando cómo la integración de distintas tecnologías puede ayudarnos a superar los desafíos de la robótica competitiva.

3. Gestión de la movilidad

3.1. Sistema de tracción y desplazamiento

El mecanismo de desplazamiento del robot está diseñado para proporcionar un movimiento controlado y una respuesta adecuada durante los recorridos de la pista. Para ello, se utiliza un sistema de tracción en las dos ruedas traseras, mientras que la orientación del vehículo se controla mediante las ruedas delanteras, accionadas por un servomotor S0009M.

Esta distribución permite separar las funciones de propulsión y dirección, facilitando el control de las trayectorias y la ejecución de maniobras durante los desafíos de la competencia.

3.2. Motores de tracción

Para impulsar el vehículo, se seleccionaron motores de corriente continua N20, debido a su tamaño reducido y a su facilidad de integración en estructuras robóticas compactas.

Características técnicas del motor N20

- Voltaje nominal: 6 V
- Velocidad sin carga: 500 RPM
- Par de bloqueo: 0.15 kg·cm
- Corriente indicada: 0.023 A
- Relación de engranajes: 1:100

Justificación de la elección

La selección de estos motores responde a la necesidad de mantener un diseño compacto y reducir el espacio ocupado por los componentes de propulsión. Su caja reductora permite adaptar la velocidad de giro a las necesidades de desplazamiento del robot.

Además, los encoders incorporados permiten obtener información sobre el movimiento de los motores, lo que puede utilizarse para estimar el desplazamiento de las ruedas y mejorar el control de velocidad. Esta retroalimentación resulta útil para ajustar el comportamiento del vehículo durante las pruebas y favorecer movimientos más consistentes.

3.3. Mecanismo de transmisión diferencial

La transmisión del movimiento hacia las ruedas traseras se realiza mediante un mecanismo diferencial construido con engranajes LEGO. Su función es permitir que ambas ruedas giren a velocidades diferentes cuando el robot realiza una curva.

Esta diferencia de velocidad ayuda a reducir el arrastre de las llantas y facilita los cambios de trayectoria. De esta manera, el mecanismo contribuye a mejorar la maniobrabilidad del vehículo, especialmente al atravesar curvas cerradas o ejecutar maniobras de estacionamiento en paralelo.

La combinación de los motores N20, la lectura de los encoders y la transmisión diferencial integra tres elementos importantes del sistema de movilidad: generación de movimiento, seguimiento de su comportamiento y distribución de la tracción. En conjunto, estos componentes permiten desarrollar una plataforma que puede ajustarse mediante pruebas para responder a las exigencias de la pista de competición.