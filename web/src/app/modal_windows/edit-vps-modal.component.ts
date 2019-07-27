import { Component } from '@angular/core';
import { MatBottomSheetRef } from '@angular/material';
import { VpsManagementComponent } from '../vps-management/vps-management.component'
import { FormControl, Validators } from '@angular/forms';
import { RequestsService } from '../requests.service';

@Component({
  selector: 'edit-vps-modal.component',
  templateUrl: 'edit-vps-modal.component.html',
})

export class EditVpsModal {

  ipPattern =
    "(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)";

  isLoading: boolean = false;

  ansibleHostFormControl = new FormControl('', [
    Validators.pattern(this.ipPattern),
  ]);
  ansibleUserFormControl = new FormControl('', [
    Validators.required,

  ]);
  hostnameFormControl = new FormControl('', [
    Validators.required,

  ]);
  portFormControl = new FormControl('', [
    Validators.required,
  ]);


  constructor(private _bottomSheetRef: MatBottomSheetRef<VpsManagementComponent>, private http: RequestsService) { }

  addVPS() {
    this.isLoading = true;
    this.http.addVPS(
      {
        hostname: this.hostnameFormControl.value,
        parameters: {
          ansible_host: this.ansibleHostFormControl.value,
          ansible_user: this.ansibleUserFormControl.value,
          ansible_port: this.portFormControl.value,
        }
      }).subscribe((data) => {
        this.isLoading = false;
        alert(data.message);
        this._bottomSheetRef.dismiss();
      },
        err => {
          this.isLoading = false;
          alert(err.error.message);
          this._bottomSheetRef.dismiss();
        }
      )
  }
}