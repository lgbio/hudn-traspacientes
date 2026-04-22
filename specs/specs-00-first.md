# Patient Transfer Services Registry

## Goal
- I want to create a django web app for filling a form with multiple fields. 

- Currently this data is filled using a excel spreadsheet. 

- The info of each row of the form is a record of a patient transfer service including the following columns (in spanish):
´´´
 Column names           ║ Value example                          ║
 -----------------------+----------------------------------------║
 FECHA                  ║ 3/1/2026                               ║
 HORA REPORTE           ║ 02:27                                  ║
 HORA DE EGRESO         ║ 13:42                                  ║
 HORA DE INGRESO        ║ 16:55                                  ║
 NOMBRE DE PACIENTE     ║ VALERIA GOMEZ MUÑOZ                    ║
 DOCUMENTO              ║ 1110049503                             ║
 SERVICIO               ║ HOSPITAL INFANTIL LOS ANGELES  257     ║
 QUIEN REPORTA          ║ RETORNO                                ║
 DESTINO                ║ MEDINUCLEAR LA AURORA                  ║
 PROCEDIMIENTO          ║ RESONANCIA CEREBRAL BAJO SEDACION      ║
 MEDICO                 ║ DRA. KARINA RODRIGUEZ                  ║
 CONDUCTOR              ║ LUIS JIMENEZ RAMOS                     ║
 RADIO OPERADOR         ║ AYDA SANTANDER MATTA                   ║
 AMBULANCIA DE TRASLADO ║ OLO-248                                ║
 OBSERVACIÓN            ║ RETORNAN PACIENTE A HILA TAM Y CAMILLA ║
´´´

- In the current spreadsheet, user saves this info by each month of the year where months corresponds to individual sheets. Aprox. 300 records by month (sheet).

- Each month, the user sends a report of all the records as excel sheet file and pdf.

- The users of the system are normal users (FUNCIONARIO) and a staff user (DIRECTOR). 

- The DIRECTOR can create reports and manage user: create, remove, change password. 

- The FUNCIONARIO can only change its password, and generate reports, similarly for the director.

- The DIRECTOR can close the records of a month so these record becomes as read only (not write/update/delete).

## User Interaction and Flow
- User types the app URL in the browser
- If not previous session, the app responds with a login screen, as:

´´´
| REGISTRO DE PACIENTES |
|-----------------------|
| hospital logo (.png)  |
|                       |
| Usuario: [XXXXX]      |
| Contraseña: [YYYY]    |
|                       |
| Recuperar Contraseña  |
|                       |
| [Ingresar] [Cancelar] |

´´´
- If pressed 'Ingresar' then it shows the main view, that contains:
	* Title sidebar (top right) with widgets to select month and days range:
		* Mes: It is a listbox for selecting the month for adding/viewing records. By default current month. It validates that dates are for previous or current month.
		* Día: with 'Desde' and 'Hasta': Range of days to view the records. Similarly to month, it validates accepted days.
	* Left Sidebar with:
		- User info panel (top left sidebar) with Usuario (current user), Fecha (current date), and Salir (logout). 
		- Options panel (center left sidebar) with Reportes and Gestion Menus. 
		- Reportes shows two options: 
			* Excel: That creates an excel file for the current table (or current month)
			* PDF: That creates an excel file for the current table (or current month)
		- Gestion show two options:
			* Contraseña: For changing contraseña. For both roles: DIRECTOR and FUNCIONARIO.
			* Usuarios  : For user management (create, delete, password) only enable for DIRECTOR.
	* Central panel: table with the header columns and the rows (edited enabled) for each record. Where the first column 'Acciones' is an array of small buttons (icons) with the following buttons:
		- [e] : 'Editar' that shows a modal dialog for filling the current selected row but in a vertical layout with a set of pairs of label : input field. At the end there is a pais of buttons for save ('Guardar') or cancel ('Cancelar')
		- [x] : 'Eliminar' that deletes the current row showing a warning message of accept or cancel.
		- [+] : 'Adicionar' that adds a new row below the current one ready for edit and with the same "Acciones" array.

´´´
---------------|-----------------------------------------------------------------------------------------
Usuario: XXXX  |        REGISTRO DE SERVICIO DE TRASLADO DE PACIENTES MES ABRIL 2026                     |
Fecha  : WWWW  |   Mes: [AAAA]           Día: Desde: [12/04/2026] hasta [12/04/2026]                     |
   [Salir ]    |                                                                                         |
---------------|-----------------------------------------------------------------------------------------|
               | Acciones  | Fecha | Hora    | Hora   | Hora    | Nombre del Paciente | Documento | ...  |
> Reportes     |           |       | Reporte | Egreso | Ingreso |                     |           | ...  |
  - Excel      |-----------------------------------------------------------------------------------------| 
  - PDF        | [e][x][+] | aaaaa | bbbbbb  | ccccc  | dddddd  | eeeeeeeeeeeeeeeeee  | 1234444   | ...  |
               | [e][x][+] | aaaa1 | bbbbb1  | cccc1  | ddddd1  | eeeeeeeeeeeeeeeee1  | 1234441   | ...  |
 > Gestion:    | [e][x][+] | aaaa2 | bbbbb2  | cccc2  | ddddd2  | eeeeeeeeeeeeeeeee2  | 1234442   | ...  |
  - Contraseña | [e][x][+] | aaaa3 | bbbbb3  | cccc3  | ddddd3  | eeeeeeeeeeeeeeeee3  | 1234443   | ...  |
  - Usuarios   | [e][x][+] | aaaa4 | bbbbb4  | cccc4  | ddddd4  | eeeeeeeeeeeeeeeee4  | 1234444   | ...  |
               | [e][x][+] | aaaa5 | bbbbb5  | cccc5  | ddddd5  | eeeeeeeeeeeeeeeee5  | 1234445   | ...  |
               | [e][x][+] | aaaa6 | bbbbb6  | cccc6  | ddddd6  | eeeeeeeeeeeeeeeee6  | 1234446   | ...  |
               |...                                                                                      |
               |...                                                                                      |
---------------------------------------------------------------------------------------------------------

´´´

## Design
- It will be implemented python django framework.
- Use a local DB for the MVP for saving month records info.
- Tables can be editable and the with good look and feel, maybe as an excel sheet.
- Try to avoid, if possible, complex frontends libraries, maybe django elements but with good look and feel.
- Use a simply local DB (sqlite) if possible, if not, then use postgress.

