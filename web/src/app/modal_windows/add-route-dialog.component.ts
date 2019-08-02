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

    isLoading: boolean = false;
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
        this.isLoading = true;
        this.http.addRoute(
            {
                hostname: this.data.hostname,
                destination: this.destinationFormControl.value,
                source: this.sourceFormControl.value,
                description: this.descriptionFormControl.value
            }).subscribe((data) => {
                // let message = "Status:" + data.status + 'Output:' + data.message;
                alert("Route is added");
                this.isLoading = false;
                this.dialogRef.close();
            },
                err => {
                    this.isLoading = false;
                    alert(err.error.message);
                    this.dialogRef.close();
                }
            )
    }
}