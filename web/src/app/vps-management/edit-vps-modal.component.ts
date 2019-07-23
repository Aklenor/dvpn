import { Inject, Component } from '@angular/core';
import { MAT_BOTTOM_SHEET_DATA } from '@angular/material';
import { MatBottomSheet, MatBottomSheetRef } from '@angular/material';
import { VpsManagementComponent } from './vps-management.component'
import { FormControl, FormGroupDirective, NgForm, Validators } from '@angular/forms';
import { RequestsService } from '../requests.service';

@Component({
  selector: 'edit-vps-modal.component',
  templateUrl: 'edit-vps-modal.component.html',
})

export class EditVpsModal {

  ansibleHostFormControl = new FormControl('', [
    Validators.required,
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
    this.http.addVPS(
      {
        hostname: this.hostnameFormControl.value,
        parameters: {
          ansible_host: this.ansibleHostFormControl.value,
          ansible_user: this.ansibleUserFormControl.value,
          ansible_port: this.portFormControl.value,
        }
      }).subscribe(data => {
        console.log(data)
      });
    this._bottomSheetRef.dismiss();
  }
}