## segway (%[^ ]+%) run (%[0-9a-f]{32}%) at (%[0-9]{4}%)-(%[0-9]{2}%)-(%[0-9]{2}%) (%[0-9]{2}%):(%[0-9]{2}%):(%[0-9]{2}%).(%[0-9]{1,}%)
(%[^ ]+%)/gmtkTriangulate -cppCommandOptions (%'(?=.*-\bDCARD_SEG=2\b)(?=.*-\bDCARD_FRAMEINDEX=2000000\b)(?=.*-\bDCARD_SUBSEG=2\b)(?=.*-\bDSEGTRANSITION_WEIGHT_SCALE=1\.0\b).*'%) -outputTriangulatedFile traindir/triangulation/segway.str.2.2.trifile -strFile traindir/segway.str -verbosity 0
(%[^ ]+%)/segway-task run train '' chr1 0 8000 1 0 ../simplesubseg.genomedata,../simplesubseg.genomedata asinh_norm 0,1 True '[((%\d+%), (%\d+%))]' '[(%\d%)]' -base 3 -componentCache F -cppCommandOptions (%'(?=.*-\bDCARD_SEG=2\b)(?=.*-\bDCARD_FRAMEINDEX=2000000\b)(?=.*-\bDCARD_SUBSEG=2\b)(?=.*-\bDSEGTRANSITION_WEIGHT_SCALE=1\.0\b).*'%) -deterministicChildrenStore F -dirichletPriors T -fmt1 binary -fmt2 binary -hashLoadFactor 0.98 -inputMasterFile traindir/params/input.master -island T -iswp1 F -iswp2 F -jtFile traindir/log/jt_info.txt -lldp 0.001 -lst 100000 -maxEmIters 1 -nf1 2 -nf2 0 -ni1 0 -ni2 4 -objsNotToTrain traindir/auxiliary/dont_train.list -obsNAN T -of1 traindir/observations/float32.list -of2 traindir/observations/int.list -storeAccFile traindir/accumulators/acc.0.0.bin -strFile traindir/segway.str -triFile traindir/triangulation/segway.str.2.2.trifile -trrng 0 -verbosity 0
(%[^ ]+%)/segway-task run bundle-train '' 0 0 0 1 0 -base 3 -componentCache F -cppCommandOptions (%'(?=.*-\bDCARD_SEG=2\b)(?=.*-\bDOUTPUT_PARAMS_FILENAME=traindir/params/params\.0\.params\.0\b)(?=.*-\bDCARD_FRAMEINDEX=2000000\b)(?=.*-\bDCARD_SUBSEG=2\b)(?=.*-\bDSEGTRANSITION_WEIGHT_SCALE=1\.0\b).*'%) -deterministicChildrenStore F -fmt1 binary -fmt2 binary -hashLoadFactor 0.98 -inputMasterFile traindir/params/input.master -island T -iswp1 F -iswp2 F -jtFile traindir/log/jt_info.txt -llStoreFile traindir/likelihood/likelihood.ll -lldp 0.001 -loadAccFile traindir/accumulators/acc.0.@D.bin -loadAccRange 0 -lst 100000 -maxEmIters 1 -nf1 2 -nf2 0 -ni1 0 -ni2 4 -objsNotToTrain traindir/auxiliary/dont_train.list -obsNAN T -of1 traindir/observations/float32.list -of2 traindir/observations/int.list -outputMasterFile traindir/params/output.master -strFile traindir/segway.str -triFile traindir/triangulation/segway.str.2.2.trifile -trrng nil -verbosity 0
(%[^ ]+%)/segway-task run train '' chr1 0 8000 1 0 ../simplesubseg.genomedata,../simplesubseg.genomedata asinh_norm 0,1 True '[((%\d+%), (%\d+%))]' '[(%\d%)]' -base 3 -componentCache F -cppCommandOptions (%'(?=.*-\bDCARD_SEG=2\b)(?=.*-\bDINPUT_PARAMS_FILENAME=traindir/params/params\.0\.params\.0\b)(?=.*-\bDCARD_FRAMEINDEX=2000000\b)(?=.*-\bDCARD_SUBSEG=2\b)(?=.*-\bDSEGTRANSITION_WEIGHT_SCALE=1\.0\b).*'%) -deterministicChildrenStore F -dirichletPriors T -fmt1 binary -fmt2 binary -hashLoadFactor 0.98 -inputMasterFile traindir/params/input.master -island T -iswp1 F -iswp2 F -jtFile traindir/log/jt_info.txt -lldp 0.001 -lst 100000 -maxEmIters 1 -nf1 2 -nf2 0 -ni1 0 -ni2 4 -objsNotToTrain traindir/auxiliary/dont_train.list -obsNAN T -of1 traindir/observations/float32.list -of2 traindir/observations/int.list -storeAccFile traindir/accumulators/acc.0.0.bin -strFile traindir/segway.str -triFile traindir/triangulation/segway.str.2.2.trifile -trrng 0 -verbosity 0
(%[^ ]+%)/segway-task run bundle-train '' 0 0 0 1 0 -base 3 -componentCache F -cppCommandOptions (%'(?=.*-\bDCARD_SEG=2\b)(?=.*-\bDOUTPUT_PARAMS_FILENAME=traindir/params/params\.0\.params\.1\b)(?=.*-\bDINPUT_PARAMS_FILENAME=traindir/params/params\.0\.params\.0\b)(?=.*-\bDCARD_FRAMEINDEX=2000000\b)(?=.*-\bDCARD_SUBSEG=2\b)(?=.*-\bDSEGTRANSITION_WEIGHT_SCALE=1\.0\b).*'%) -deterministicChildrenStore F -fmt1 binary -fmt2 binary -hashLoadFactor 0.98 -inputMasterFile traindir/params/input.master -island T -iswp1 F -iswp2 F -jtFile traindir/log/jt_info.txt -llStoreFile traindir/likelihood/likelihood.ll -lldp 0.001 -loadAccFile traindir/accumulators/acc.0.@D.bin -loadAccRange 0 -lst 100000 -maxEmIters 1 -nf1 2 -nf2 0 -ni1 0 -ni2 4 -objsNotToTrain traindir/auxiliary/dont_train.list -obsNAN T -of1 traindir/observations/float32.list -of2 traindir/observations/int.list -outputMasterFile traindir/params/output.master -strFile traindir/segway.str -triFile traindir/triangulation/segway.str.2.2.trifile -trrng nil -verbosity 0
(%[^ ]+%)/segway-task run train '' chr1 0 8000 1 0 ../simplesubseg.genomedata,../simplesubseg.genomedata asinh_norm 0,1 True '[((%\d+%), (%\d+%))]' '[(%\d%)]' -base 3 -componentCache F -cppCommandOptions (%'(?=.*-\bDCARD_SEG=2\b)(?=.*-\bDINPUT_PARAMS_FILENAME=traindir/params/params\.0\.params\.1\b)(?=.*-\bDCARD_FRAMEINDEX=2000000\b)(?=.*-\bDCARD_SUBSEG=2\b)(?=.*-\bDSEGTRANSITION_WEIGHT_SCALE=1\.0\b).*'%) -deterministicChildrenStore F -dirichletPriors T -fmt1 binary -fmt2 binary -hashLoadFactor 0.98 -inputMasterFile traindir/params/input.master -island T -iswp1 F -iswp2 F -jtFile traindir/log/jt_info.txt -lldp 0.001 -lst 100000 -maxEmIters 1 -nf1 2 -nf2 0 -ni1 0 -ni2 4 -objsNotToTrain traindir/auxiliary/dont_train.list -obsNAN T -of1 traindir/observations/float32.list -of2 traindir/observations/int.list -storeAccFile traindir/accumulators/acc.0.0.bin -strFile traindir/segway.str -triFile traindir/triangulation/segway.str.2.2.trifile -trrng 0 -verbosity 0
(%[^ ]+%)/segway-task run bundle-train '' 0 0 0 1 0 -base 3 -componentCache F -cppCommandOptions (%'(?=.*-\bDCARD_SEG=2\b)(?=.*-\bDOUTPUT_PARAMS_FILENAME=traindir/params/params\.0\.params\.2\b)(?=.*-\bDINPUT_PARAMS_FILENAME=traindir/params/params\.0\.params\.1\b)(?=.*-\bDCARD_FRAMEINDEX=2000000\b)(?=.*-\bDCARD_SUBSEG=2\b)(?=.*-\bDSEGTRANSITION_WEIGHT_SCALE=1\.0\b).*'%) -deterministicChildrenStore F -fmt1 binary -fmt2 binary -hashLoadFactor 0.98 -inputMasterFile traindir/params/input.master -island T -iswp1 F -iswp2 F -jtFile traindir/log/jt_info.txt -llStoreFile traindir/likelihood/likelihood.ll -lldp 0.001 -loadAccFile traindir/accumulators/acc.0.@D.bin -loadAccRange 0 -lst 100000 -maxEmIters 1 -nf1 2 -nf2 0 -ni1 0 -ni2 4 -objsNotToTrain traindir/auxiliary/dont_train.list -obsNAN T -of1 traindir/observations/float32.list -of2 traindir/observations/int.list -outputMasterFile traindir/params/output.master -strFile traindir/segway.str -triFile traindir/triangulation/segway.str.2.2.trifile -trrng nil -verbosity 0
(%[^ ]+%)/segway-task run train '' chr1 0 8000 1 0 ../simplesubseg.genomedata,../simplesubseg.genomedata asinh_norm 0,1 True '[((%\d+%), (%\d+%))]' '[(%\d%)]' -base 3 -componentCache F -cppCommandOptions (%'(?=.*-\bDCARD_SEG=2\b)(?=.*-\bDINPUT_PARAMS_FILENAME=traindir/params/params\.0\.params\.2\b)(?=.*-\bDCARD_FRAMEINDEX=2000000\b)(?=.*-\bDCARD_SUBSEG=2\b)(?=.*-\bDSEGTRANSITION_WEIGHT_SCALE=1\.0\b).*'%) -deterministicChildrenStore F -dirichletPriors T -fmt1 binary -fmt2 binary -hashLoadFactor 0.98 -inputMasterFile traindir/params/input.master -island T -iswp1 F -iswp2 F -jtFile traindir/log/jt_info.txt -lldp 0.001 -lst 100000 -maxEmIters 1 -nf1 2 -nf2 0 -ni1 0 -ni2 4 -objsNotToTrain traindir/auxiliary/dont_train.list -obsNAN T -of1 traindir/observations/float32.list -of2 traindir/observations/int.list -storeAccFile traindir/accumulators/acc.0.0.bin -strFile traindir/segway.str -triFile traindir/triangulation/segway.str.2.2.trifile -trrng 0 -verbosity 0
(%[^ ]+%)/segway-task run bundle-train '' 0 0 0 1 0 -base 3 -componentCache F -cppCommandOptions (%'(?=.*-\bDCARD_SEG=2\b)(?=.*-\bDOUTPUT_PARAMS_FILENAME=traindir/params/params\.0\.params\.3\b)(?=.*-\bDINPUT_PARAMS_FILENAME=traindir/params/params\.0\.params\.2\b)(?=.*-\bDCARD_FRAMEINDEX=2000000\b)(?=.*-\bDCARD_SUBSEG=2\b)(?=.*-\bDSEGTRANSITION_WEIGHT_SCALE=1\.0\b).*'%) -deterministicChildrenStore F -fmt1 binary -fmt2 binary -hashLoadFactor 0.98 -inputMasterFile traindir/params/input.master -island T -iswp1 F -iswp2 F -jtFile traindir/log/jt_info.txt -llStoreFile traindir/likelihood/likelihood.ll -lldp 0.001 -loadAccFile traindir/accumulators/acc.0.@D.bin -loadAccRange 0 -lst 100000 -maxEmIters 1 -nf1 2 -nf2 0 -ni1 0 -ni2 4 -objsNotToTrain traindir/auxiliary/dont_train.list -obsNAN T -of1 traindir/observations/float32.list -of2 traindir/observations/int.list -outputMasterFile traindir/params/output.master -strFile traindir/segway.str -triFile traindir/triangulation/segway.str.2.2.trifile -trrng nil -verbosity 0
(%[^ ]+%)/segway-task run train '' chr1 0 8000 1 0 ../simplesubseg.genomedata,../simplesubseg.genomedata asinh_norm 0,1 True '[((%\d+%), (%\d+%))]' '[(%\d%)]' -base 3 -componentCache F -cppCommandOptions (%'(?=.*-\bDCARD_SEG=2\b)(?=.*-\bDINPUT_PARAMS_FILENAME=traindir/params/params\.0\.params\.3\b)(?=.*-\bDCARD_FRAMEINDEX=2000000\b)(?=.*-\bDCARD_SUBSEG=2\b)(?=.*-\bDSEGTRANSITION_WEIGHT_SCALE=1\.0\b).*'%) -deterministicChildrenStore F -dirichletPriors T -fmt1 binary -fmt2 binary -hashLoadFactor 0.98 -inputMasterFile traindir/params/input.master -island T -iswp1 F -iswp2 F -jtFile traindir/log/jt_info.txt -lldp 0.001 -lst 100000 -maxEmIters 1 -nf1 2 -nf2 0 -ni1 0 -ni2 4 -objsNotToTrain traindir/auxiliary/dont_train.list -obsNAN T -of1 traindir/observations/float32.list -of2 traindir/observations/int.list -storeAccFile traindir/accumulators/acc.0.0.bin -strFile traindir/segway.str -triFile traindir/triangulation/segway.str.2.2.trifile -trrng 0 -verbosity 0
(%[^ ]+%)/segway-task run bundle-train '' 0 0 0 1 0 -base 3 -componentCache F -cppCommandOptions (%'(?=.*-\bDCARD_SEG=2\b)(?=.*-\bDOUTPUT_PARAMS_FILENAME=traindir/params/params\.0\.params\.4\b)(?=.*-\bDINPUT_PARAMS_FILENAME=traindir/params/params\.0\.params\.3\b)(?=.*-\bDCARD_FRAMEINDEX=2000000\b)(?=.*-\bDCARD_SUBSEG=2\b)(?=.*-\bDSEGTRANSITION_WEIGHT_SCALE=1\.0\b).*'%) -deterministicChildrenStore F -fmt1 binary -fmt2 binary -hashLoadFactor 0.98 -inputMasterFile traindir/params/input.master -island T -iswp1 F -iswp2 F -jtFile traindir/log/jt_info.txt -llStoreFile traindir/likelihood/likelihood.ll -lldp 0.001 -loadAccFile traindir/accumulators/acc.0.@D.bin -loadAccRange 0 -lst 100000 -maxEmIters 1 -nf1 2 -nf2 0 -ni1 0 -ni2 4 -objsNotToTrain traindir/auxiliary/dont_train.list -obsNAN T -of1 traindir/observations/float32.list -of2 traindir/observations/int.list -outputMasterFile traindir/params/output.master -strFile traindir/segway.str -triFile traindir/triangulation/segway.str.2.2.trifile -trrng nil -verbosity 0
(%[^ ]+%)/segway-task run train '' chr1 0 8000 1 0 ../simplesubseg.genomedata,../simplesubseg.genomedata asinh_norm 0,1 True '[((%\d+%), (%\d+%))]' '[(%\d%)]' -base 3 -componentCache F -cppCommandOptions (%'(?=.*-\bDCARD_SEG=2\b)(?=.*-\bDINPUT_PARAMS_FILENAME=traindir/params/params\.0\.params\.4\b)(?=.*-\bDCARD_FRAMEINDEX=2000000\b)(?=.*-\bDCARD_SUBSEG=2\b)(?=.*-\bDSEGTRANSITION_WEIGHT_SCALE=1\.0\b).*'%) -deterministicChildrenStore F -dirichletPriors T -fmt1 binary -fmt2 binary -hashLoadFactor 0.98 -inputMasterFile traindir/params/input.master -island T -iswp1 F -iswp2 F -jtFile traindir/log/jt_info.txt -lldp 0.001 -lst 100000 -maxEmIters 1 -nf1 2 -nf2 0 -ni1 0 -ni2 4 -objsNotToTrain traindir/auxiliary/dont_train.list -obsNAN T -of1 traindir/observations/float32.list -of2 traindir/observations/int.list -storeAccFile traindir/accumulators/acc.0.0.bin -strFile traindir/segway.str -triFile traindir/triangulation/segway.str.2.2.trifile -trrng 0 -verbosity 0
(%[^ ]+%)/segway-task run bundle-train '' 0 0 0 1 0 -base 3 -componentCache F -cppCommandOptions (%'(?=.*-\bDCARD_SEG=2\b)(?=.*-\bDOUTPUT_PARAMS_FILENAME=traindir/params/params\.0\.params\.5\b)(?=.*-\bDINPUT_PARAMS_FILENAME=traindir/params/params\.0\.params\.4\b)(?=.*-\bDCARD_FRAMEINDEX=2000000\b)(?=.*-\bDCARD_SUBSEG=2\b)(?=.*-\bDSEGTRANSITION_WEIGHT_SCALE=1\.0\b).*'%) -deterministicChildrenStore F -fmt1 binary -fmt2 binary -hashLoadFactor 0.98 -inputMasterFile traindir/params/input.master -island T -iswp1 F -iswp2 F -jtFile traindir/log/jt_info.txt -llStoreFile traindir/likelihood/likelihood.ll -lldp 0.001 -loadAccFile traindir/accumulators/acc.0.@D.bin -loadAccRange 0 -lst 100000 -maxEmIters 1 -nf1 2 -nf2 0 -ni1 0 -ni2 4 -objsNotToTrain traindir/auxiliary/dont_train.list -obsNAN T -of1 traindir/observations/float32.list -of2 traindir/observations/int.list -outputMasterFile traindir/params/output.master -strFile traindir/segway.str -triFile traindir/triangulation/segway.str.2.2.trifile -trrng nil -verbosity 0
