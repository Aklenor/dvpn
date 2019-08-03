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
    this.getRoutes();
  }

  getRoutes() {
    this.isLoadingResults = true;
    let arr = [];
    this.http.getRoutes().subscribe((data: any) => {
      for (let el in data.clients) {
        let routes = [];

        for (let r in data.clients[el].routes) {
          routes.push(
            {
              hostname: data.clients[el].routes[r].VPS.hostname,
              destination: data.clients[el].routes[r].destination,
            });
        }
        arr.push({ source: data.clients[el].source, routes: routes });
      }
      this.dataRoutes = arr;
      this.isLoadingResults = false;
    }
    )
  }

  // openDialog(hostname) {
  //   const dialogRef = this.dialog.open(AddRouteDialogComponent, {
  //     data: {
  //       hostname: hostname
  //     }
  //   });

  //   dialogRef.afterClosed().subscribe(result => {
  //   },
  //   );
  // }


  deleteRoute(source, destination, hostname) {
    this.isLoadingResults = true;
    this.http.deleteRoute({
      hostname: hostname,
      destination: destination,
      source: source
    }).subscribe(data => {
      alert("Route is deleted");
      this.getRoutes();
      this.isLoadingResults = false;
    },
      err => {
        alert(err.error.message);
        this.getRoutes();
        this.isLoadingResults = false;
      }
    )
  }

}
