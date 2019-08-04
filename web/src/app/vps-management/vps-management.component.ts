import { Component } from '@angular/core';
import { MatTableDataSource } from '@angular/material/table';
import { RequestsService } from '../requests.service';
import { vpsList } from '../vpsList';
// import { animate, state, style, transition, trigger } from '@angular/animations';
import { MatBottomSheet, MatBottomSheetRef } from '@angular/material/bottom-sheet';
import { EditVpsModal } from '../modal_windows/edit-vps-modal.component';
import { MatDialog } from '@angular/material/dialog';
import { AddRouteDialogComponent } from '../modal_windows/add-route-dialog.component';


@Component({
  selector: 'app-vps-management',
  templateUrl: './vps-management.component.html',
  styleUrls: ['./vps-management.component.css'],
  // animations: [
  //   trigger('detailExpand', [
  //     state('collapsed', style({ height: '0px', minHeight: '0' })),
  //     state('expanded', style({ height: '*' })),
  //     transition('expanded <=> collapsed', animate('225ms cubic-bezier(0.4, 0.0, 0.2, 1)')),
  //   ]),
  // ],
})

export class VpsManagementComponent {

  vps: vpsList[] = [];
  displayedColumns: string[] = ['hostname', 'interface', 'ip', 'location', 'status', 'configured', 'progress', 'add', 'delete'];
  dataSource;
  isLoadingResults = true;
  ipAddress: any;
  updDaemon: number;

  constructor(private http: RequestsService, private _bottomSheet: MatBottomSheet, public dialog: MatDialog) { }

  ngOnInit() {
    this.getListVPS();
    // IP Address API request
    this.http.getIpAddress().subscribe(data => { this.ipAddress = data });
  }

  // Rrequesting available VPS list. If config 'in progress' repeat request after 10 sec.
  getListVPS() {
    let isThereProgress = false;
    let arr = [];
    this.http.getVpsList().subscribe((data: vpsList[]) => {
      for (let el in data) {
        arr.push(data[el]);
      }
      this.vps = arr;
      this.dataSource = new MatTableDataSource(this.vps);
      this.isLoadingResults = false;

      for (let element in arr) {
        if (arr[element].configured == 'in progress' || arr[element].configured == 'in deletion') {
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

  openDialog(hostname) {
    const dialogRef = this.dialog.open(AddRouteDialogComponent, {
      data: {
        hostname: hostname
      }
    });


    dialogRef.afterClosed().subscribe(result => {
      this.getListVPS();
      this.http.getIpAddress().subscribe(data => { this.ipAddress = data });
    },
    );

  }


  applyFilter(filterValue: string) {
    this.dataSource.filter = filterValue.trim().toLowerCase();
  }

  deleteVps(hostname) {
    var x = confirm("Are you sure you want to delete?");
    if (x) {
      this.isLoadingResults = true;
      this.http.deleteVPS({ hostname: hostname }).subscribe(data => {
        alert(data.message);
        this.getListVPS();
        this.isLoadingResults = false;
      },
        err => {
          alert(err.error.message);
          this.getListVPS();
          this.isLoadingResults = false;
        }
      )
    }
  }

  openSnackBar() {
    this._bottomSheet.open(sshKeyOverview);
  }
}

@Component({
  selector: 'ssh-key-overview',
  template: `
  <p><b>{{key}}</b></p>
`,
})
export class sshKeyOverview {

  key: any;
  constructor(private _bottomSheetRef: MatBottomSheetRef<VpsManagementComponent>, private http: RequestsService, ) {
    this.http.getSSH().subscribe(data => this.key = data.pubkey)
  }
}