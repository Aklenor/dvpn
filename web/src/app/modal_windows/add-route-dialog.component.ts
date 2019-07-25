import { Inject, Component } from '@angular/core';
import { MatDialog, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { FormControl, Validators } from '@angular/forms';
import { RequestsService } from '../requests.service';
import { IpRoutesComponent } from '../ip-routes/ip-routes.component';

@Component({
    selector: 'add-route-dialog.component',
    templateUrl: 'add-route-dialog.component.html',
})

export class AddRouteDialogComponent {

    ipPattern =
        "(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)";

    destinationFormControl = new FormControl('', [
        Validators.required,

    ]);
    sourceFormControl = new FormControl('', [
        Validators.required,

    ]);

    descriptionFormControl = new FormControl('', [
        Validators.required,

    ]);
    constructor(public dialogRef: MatDialogRef<IpRoutesComponent>,
        @Inject(MAT_DIALOG_DATA) public data, private http: RequestsService) { }

    addRoute() {
        this.http.addRoute(
            {
                hostname: this.data,
                destination: this.destinationFormControl.value,
                source: this.sourceFormControl.value,
                descrition: this.descriptionFormControl.value
            }).subscribe((data) => {
                console.log(data.message);
                alert(data.message);
            },
                err => {
                    console.log(err.error.message),
                        alert(err.error.message);
                }
            )
    }
}