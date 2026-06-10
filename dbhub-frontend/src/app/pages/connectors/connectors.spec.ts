import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Connectors } from './connectors';

describe('Connectors', () => {
  let component: Connectors;
  let fixture: ComponentFixture<Connectors>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Connectors],
    }).compileComponents();

    fixture = TestBed.createComponent(Connectors);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
