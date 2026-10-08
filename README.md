# CyberBots


CyberBots es un equipo de robótica que participa en WRO Future Engineers, donde desarrollamos vehículos autónomos capaces de interpretar su entorno y tomar decisiones de forma independiente.

En este proyecto combinamos programación, electrónica, diseño mecánico y visión por computadora para diseñar, construir y mejorar nuestro vehículo.

Este repositorio documenta nuestro proceso de desarrollo, desde el diseño y ensamblaje hasta la programación, las pruebas y las mejoras realizadas durante el proyecto.



[Nuestro equipo](#Nuetsro-equipo)

[Misión] (#-Mision) 

     [Visión] (#-Vision)

[WRO Future Engineers] (#WRO-Future-Engineers)

[Fases del desafío] (#Fases-del-desafío)











Nuestro equipo 

Somos un equipo conformado por tres estudiantes guatemaltecos que compartimos el interés por la robótica, la tecnología y la innovación. A lo largo del proyecto, hemos trabajado de manera colaborativa, aportando nuestras habilidades y conocimientos en las diferentes áreas necesarias para desarrollar nuestro vehículo.

Integrantes

Sergio Andrés Carrera Canel

Estudiante guatemalteco de cuarto bachillerato en Ciencias y Letras con Orientación en Computación. Se caracteriza por ser responsable, analítico y enfocado en sus objetivos. Dentro del equipo, está a cargo principalmente de la programación y lógica de funcionamiento del vehículo.

Stefany Andrea Tobar de Paz

Estudiante guatemalteca de cuarto bachillerato en Ciencias y Letras con Orientación en Computación. Se caracteriza por ser responsable, organizada y comprometida con el trabajo en equipo. Dentro del proyecto, está a cargo principalmente de la electrónica y parte del desarrollo visual.

Jason Arturo Carrera Garrido

Estudiante guatemalteco de cuarto bachillerato en Ciencias y Letras con Orientación en Diseño Gráfico. Se caracteriza por su creatividad, disposición para colaborar y capacidad para aportar al trabajo en equipo. Está encargado principalmente del diseño y desarrollo visual del proyecto.



Misión
Desarrollar soluciones robóticas autónomas mediante la integración de programación, electrónica, diseño y trabajo en equipo, aplicando nuestros conocimientos para crear un vehículo eficiente, preciso y capaz de responder a diferentes desafíos.


 Visión
Consolidarnos como un equipo guatemalteco de robótica reconocido por nuestra innovación, disciplina y capacidad de aprendizaje, buscando mejorar continuamente nuestras habilidades y representar a Guatemala con proyectos tecnológicos de calidad.


WRO Future Engineers

Future Engineers es una categoría de la World Robot Olympiad (WRO) en la que los participantes diseñan, construyen y programan un vehículo autónomo capaz de completar diferentes desafíos dentro de una pista. El vehículo debe interpretar su entorno, tomar decisiones y ejecutar sus movimientos sin intervención humana.

Para nosotros, esta categoría representa una oportunidad para aplicar nuestros conocimientos en un proyecto real, poner a prueba nuestras habilidades y mejorar constantemente nuestro vehículo mediante pruebas y ajustes.

Fases del desafío
El recorrido está compuesto por tres fases, en las que el vehículo debe interpretar diferentes elementos de la pista y responder de manera autónoma.

1. Guía por color — Azul y naranja

En esta primera fase, el vehículo utiliza la cámara frontal para identificar las franjas de color que indican la dirección del recorrido. El sistema analiza la primera franja detectada y determina el giro correspondiente:
Naranja 🟧: giro hacia la derecha.
Azul 🟦: giro hacia la izquierda.

2. Detección y evasión de obstáculos — Rojo y verde

En la segunda fase, el vehículo debe detectar los cubos que se encuentran en la pista y determinar la maniobra necesaria para evitarlos.
Cubo rojo 🟥: giro hacia la derecha.
Cubo verde 🟩: giro hacia la izquierda.
La información obtenida por las cámaras permite identificar el obstáculo y seleccionar la dirección correspondiente.

3. Parqueo autónomo — Área rosada 🩷

En la última fase, el vehículo debe reconocer el área delimitada por tablas rosadas y realizar la maniobra necesaria para ingresar y posicionarse dentro del espacio de parqueo.

En esta etapa se busca que el vehículo pueda controlar su movimiento y terminar el recorrido de manera precisa y completamente autónoma.