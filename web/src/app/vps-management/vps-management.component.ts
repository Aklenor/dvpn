import { Component } from '@angular/core';
import { MatTableDataSource } from '@angular/material/table';
import { RequestsService } from '../requests.service';
import { vpsList } from '../vpsList';
import { animate, state, style, transition, trigger } from '@angular/animations';

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
  displayedColumns: string[] = ['hostname', 'interface', 'ip', 'location', 'status', 'edit', 'delete'];
  dataSource;
  isLoadingResults = true;

  constructor(private http: RequestsService) { }

  ngOnInit() {
    let arr = [];
    this.http.getVpsList().subscribe((data: vpsList[]) => {
      for (let el in data) {
        arr.push(data[el]);
      }
      this.vps = arr;
      console.log(this.vps)
      this.dataSource = new MatTableDataSource(this.vps);
      this.isLoadingResults = false;

    }
    )
  }
  applyFilter(filterValue: string) {
    this.dataSource.filter = filterValue.trim().toLowerCase();
  }

  deleteVps(hostname) {
    console.log(hostname);
  }

  editVps(hostname) {
    console.log(hostname);
  }
}