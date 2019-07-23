import { Inject, Component } from '@angular/core';
import { MatTableDataSource } from '@angular/material/table';
import { RequestsService } from '../requests.service';
import { vpsList } from '../vpsList';
import { animate, state, style, transition, trigger } from '@angular/animations';
import { MatBottomSheet, MatBottomSheetRef } from '@angular/material/bottom-sheet';
import {EditVpsModal} from './edit-vps-modal.component'

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
  displayedColumns: string[] = ['hostname', 'interface', 'ip', 'location', 'status', 'configured', 'chooseVPS','edit', 'delete'];
  dataSource;
  isLoadingResults = true;
  ipAddress: any;
  constructor(private http: RequestsService, private _bottomSheet: MatBottomSheet) { }

  ngOnInit() {
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
    }
    )
    this.http.getIpAddress().subscribe( data => { this.ipAddress=data });
  }

  openBottomSheet(hostname): void {
    this._bottomSheet.open(EditVpsModal,  {
      data: hostname });
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

  chooseVPS(hostname){
    this.http.chooseVPS({data:hostname}).subscribe(data => {
      console.log(`Choose vps ${data}`);
    })
  }
}