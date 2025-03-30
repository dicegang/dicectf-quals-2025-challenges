library(cells) {
  cell(BUF) {
    area: 6;
    pin(A) { direction: input; }
    pin(Y) { direction: output;
              function: "A"; }
  }
  cell(NOR1) {
    area: 4;
    pin(A) { direction: input; }
    pin(Y) { direction: output;
              function: "A'"; }
   }
  cell(NOR2) {
    area: 4;
    pin(A) { direction: input; }
    pin(B) { direction: input; }
    pin(Y) { direction: output; 
      function: "(A+B)'"; }
  }
  cell(NOR3) {
    area: 4;
    pin(A) { direction: input; }
    pin(B) { direction: input; }
    pin(C) { direction: input; }
    pin(Y) { direction: output; 
      function: "(A+B+C)'"; }
  }
  cell(NOR4) {
    area: 4;
    pin(A) { direction: input; }
    pin(B) { direction: input; }
    pin(C) { direction: input; }
    pin(D) { direction: input; }
    pin(Y) { direction: output; 
      function: "(A+B+C+D)'"; }
  }
  cell(NOR5) {
    area: 4;
    pin(A) { direction: input; }
    pin(B) { direction: input; }
    pin(C) { direction: input; }
    pin(D) { direction: input; }
    pin(E) { direction: input; }
    pin(Y) { direction: output; 
      function: "(A+B+C+D+E)'"; }
  }
  cell(NOR6) {
    area: 4;
    pin(A) { direction: input; }
    pin(B) { direction: input; }
    pin(C) { direction: input; }
    pin(D) { direction: input; }
    pin(E) { direction: input; }
    pin(F) { direction: input; }
    pin(Y) { direction: output; 
      function: "(A+B+C+D+E+F)'"; }
  }
  cell(DFF_PP0) {
		ff(IQ, IQN) {
			clocked_on: "C";
			next_state: "D";
			clear: "R";
		}
		pin(D) { direction: input; }
		pin(R) { direction: input; }
		pin(C) { direction: input; clock: true; }
		pin(Q) { direction: output; function: "IQ"; }
	}
}
