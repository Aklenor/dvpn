import { Component, OnInit } from '@angular/core';
import { RequestsService } from '../requests.service';
import { vpsList } from '../vpsList';
import { MatDialog } from '@angular/material/dialog';
import { AddRouteDialogComponent } from '../modal_windows/add-route-dialog.component';

@Component({
  selector: 'app-ip-routes',
  templateUrl: './ip-routes.component.html',
  styleUrls: ['./ip-routes.component.css']
})
export class IpRoutesComponent implements OnInit {

  dataRoutes = [];
  isLoadingResults = true;

  constructor(private http: RequestsService, public dialog: MatDialog) { }

  ngOnInit() {
    this.getListVPS();
  }

  getListVPS() {
    this.isLoadingResults = true;
    let arr = [];
    this.http.getVpsList().subscribe((data: vpsList[]) => {
      for (let el in data) {
        arr.push(data[el]);
      }
      this.dataRoutes = arr;
      this.isLoadingResults = false;
    }
    )
  }

  openDialog(hostname) {
    const dialogRef = this.dialog.open(AddRouteDialogComponent, {
      data: {
        hostname: hostname
      }
    });

    dialogRef.afterClosed().subscribe(result => {
      this.getListVPS();
    },
    );
  }


  deleteRoute(element, hostname) {
    this.isLoadingResults = true;
    this.http.deleteRoute({
      hostname: hostname,
      description: element.description,
      destination: element.destination,
      source: element.source
    }).subscribe(data => {
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
