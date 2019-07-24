import { Inject, Component } from '@angular/core';
import { MatTableDataSource } from '@angular/material/table';
import { RequestsService } from '../requests.service';
import { vpsList } from '../vpsList';
import { animate, state, style, transition, trigger } from '@angular/animations';
import { MatBottomSheet, MatBottomSheetRef } from '@angular/material/bottom-sheet';
import { EditVpsModal } from './edit-vps-modal.component'
import { interval, Observable } from 'rxjs';
import { mergeMap, takeWhile, concatMap } from "rxjs/operators";
import { Type } from '@angular/compiler';

@Component({
  selector: 'app-vps-management',
  templateUrl: './vps-management.component.html',
  styleUrls: ['./vps-management.component.css'],
  animations: [
    trigger('detailExpand', [
      state('collapsed', style({ height: '0px', minHeight: '0' })),
      state('expanded', style({ height: '*' })),
      transition('expanded <=> collapsed', animate('225ms cubic-bezier(0.4, 0.0, 0.2, 1)')),
    ]),
  ],
})

export class VpsManagementComponent {

  vps: vpsList[] = [];
  displayedColumns: string[] = ['hostname', 'interface', 'ip', 'location', 'status', 'configured', 'edit', 'delete'];
  dataSource;
  isLoadingResults = true;
  ipAddress: any;
  updDaemon: number;

  constructor(private http: RequestsService, private _bottomSheet: MatBottomSheet) { }

  ngOnInit() {
    this.getListVPS();

    // IP Address API request
    this.http.getIpAddress().subscribe(data => { this.ipAddress = data });
  }

  // Rrequesting available VPS list
  getListVPS() {
    let isThereProgress = false;
    let arr = [];
    this.http.getVpsList().subscribe((data: vpsList[]) => {
      for (let el in data) {
        arr.push(data[el]);
      }
      this.vps = arr;
      console.log(`edited`, this.vps);
      console.log(`raw`, data);
      this.dataSource = new MatTableDataSource(this.vps);
      this.isLoadingResults = false;

      for (let element in arr) {
        if (arr[element].configured == 'in progress') {
          isThereProgress = true;
          if (!this.updDaemon) {
            this.updDaemon = window.setInterval(() => this.getListVPS(), 10000);
          }
          break;
        }
      }
      if (!isThereProgress) {
        clearInterval(this.updDaemon)
      }
    })
  }

  openBottomSheet(): void {
    this._bottomSheet._openedBottomSheetRef = this._bottomSheet.open(EditVpsModal);
    this._bottomSheet._openedBottomSheetRef.afterDismissed().subscribe(data => { this.getListVPS(); }
    );
  }


  applyFilter(filterValue: string) {
    this.dataSource.filter = filterValue.trim().toLowerCase();
  }

  deleteVps(hostname) {
    console.log(hostname);
  }

  // OPTIONAL:
  editVps(hostname) {
    console.log(hostname);
  }
}