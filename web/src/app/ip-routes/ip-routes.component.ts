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

  dataRoutes;
  isLoadingResults = true;

  constructor(private http: RequestsService, public dialog: MatDialog) { }

  ngOnInit() {
    let arr = [];
    this.http.getVpsList().subscribe((data: vpsList[]) => {
      for (let el in data) {
        arr.push(data[el]);
      }
      this.dataRoutes = arr;
      console.log(this.dataRoutes);
      this.isLoadingResults = false;
    }
    )
  }

  openDialog(hostname) {
    const dialogRef = this.dialog.open(AddRouteDialogComponent, {
      data : hostname
    });

    dialogRef.afterClosed().subscribe(result => {
      console.log(`Dialog result: ${result}`);
    });
  }

}
