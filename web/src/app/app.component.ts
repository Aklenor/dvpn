import { Component } from '@angular/core';


@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})

export class AppComponent {
  constructor() { }

  goMonitoring() {
    window.open('http://10.1.1.240:80', "_blank");
  }

}
