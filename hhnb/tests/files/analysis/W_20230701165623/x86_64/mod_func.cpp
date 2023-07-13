#include <stdio.h>
#include "hocdec.h"
extern int nrnmpi_myid;
extern int nrn_nobanner_;
#if defined(__cplusplus)
extern "C" {
#endif

extern void _cacumm_reg(void);
extern void _cagk_reg(void);
extern void _cal2_reg(void);
extern void _can2_reg(void);
extern void _cat_reg(void);
extern void _h_reg(void);
extern void _kadist_reg(void);
extern void _kaprox_reg(void);
extern void _kca_reg(void);
extern void _kdb_reg(void);
extern void _kdrbca1_reg(void);
extern void _kmb_reg(void);
extern void _na3n_reg(void);

void modl_reg() {
  if (!nrn_nobanner_) if (nrnmpi_myid < 1) {
    fprintf(stderr, "Additional mechanisms from files\n");
    fprintf(stderr, " \"mechanisms/cacumm.mod\"");
    fprintf(stderr, " \"mechanisms/cagk.mod\"");
    fprintf(stderr, " \"mechanisms/cal2.mod\"");
    fprintf(stderr, " \"mechanisms/can2.mod\"");
    fprintf(stderr, " \"mechanisms/cat.mod\"");
    fprintf(stderr, " \"mechanisms/h.mod\"");
    fprintf(stderr, " \"mechanisms/kadist.mod\"");
    fprintf(stderr, " \"mechanisms/kaprox.mod\"");
    fprintf(stderr, " \"mechanisms/kca.mod\"");
    fprintf(stderr, " \"mechanisms/kdb.mod\"");
    fprintf(stderr, " \"mechanisms/kdrbca1.mod\"");
    fprintf(stderr, " \"mechanisms/kmb.mod\"");
    fprintf(stderr, " \"mechanisms/na3n.mod\"");
    fprintf(stderr, "\n");
  }
  _cacumm_reg();
  _cagk_reg();
  _cal2_reg();
  _can2_reg();
  _cat_reg();
  _h_reg();
  _kadist_reg();
  _kaprox_reg();
  _kca_reg();
  _kdb_reg();
  _kdrbca1_reg();
  _kmb_reg();
  _na3n_reg();
}

#if defined(__cplusplus)
}
#endif
