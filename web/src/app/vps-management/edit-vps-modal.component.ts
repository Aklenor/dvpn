import { Inject, Component } from '@angular/core';
import {MAT_BOTTOM_SHEET_DATA} from '@angular/material';
import {MatBottomSheet, MatBottomSheetRef} from '@angular/material';
import {VpsManagementComponent} from './vps-management.component'

@Component({
    selector: 'edit-vps-modal.component',
    templateUrl: 'edit-vps-modal.component.html',
  })
  
  export class EditVpsModal {
    constructor(@Inject(MAT_BOTTOM_SHEET_DATA) public data: any, private _bottomSheetRef: MatBottomSheetRef<VpsManagementComponent>) { }
  
    openLink(event: MouseEvent): void {
      this._bottomSheetRef.dismiss();
      event.preventDefault();
    }
  }