# SPEC-076 · Yellowdata como sitio público en el Droplet

> Curso: Gestión de Proyectos en IA y CD (551475) · Story points: **3** · Responsable: Daniel
> Silva · Continúa [SPEC-075](../075-despliegue-droplet/spec.md) · Decisión:
> [ADR-034](../../../docs/decisiones/ADR-034-despliegue-droplet-caddy.md). Guía:
> [`docs/despliegue.md`](../../../docs/despliegue.md).

## Problema
El dominio principal del Droplet mostraba el frontend React del curso (panel del equipo). El
producto que ve el cliente es Yellowdata (Next.js, robot Yelo), que vive en su propio repositorio.

## Requisitos
- **R076.1** `https://$DOMINIO` DEBE servir Yellowdata; el frontend del curso pasa a
  `https://app.$DOMINIO` y la API sigue en `https://api.$DOMINIO`.
- **R076.2** Yellowdata DEBE llamar a la API por la red interna de Docker (`http://api:8000`), sin
  publicar puertos propios.
- **R076.3** La imagen DEBE venir del Container Registry del proyecto `daalrasi/yellowdata`, que la
  construye en su propio pipeline; el deploy de este repositorio la descarga con su `CI_JOB_TOKEN`.
- **R076.4** El deploy DEBE verificar por HTTPS las tres URL.

## Criterios de aceptación
- **AC1** · **Dado** un deploy en verde, **cuando** se abre `https://$DOMINIO`, **entonces** carga
  Yellowdata y su chat responde con la API del Droplet.
- **AC2** · `https://app.$DOMINIO` sigue mostrando el panel del equipo.

## Fuera de alcance
Publicación de Yellowdata en cPanel (`www.yellowdata.com.co`), que usará la misma API pública.
